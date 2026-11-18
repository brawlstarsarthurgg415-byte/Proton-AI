"""Configurable decoder-only Transformer with top-k Mixture-of-Experts blocks.

This is a research implementation. The Android 3B profile is a design target;
do not instantiate it on a phone until a memory-efficient inference backend
and a compatible quantized checkpoint exist.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F


@dataclass(frozen=True)
class ProtonMoEConfig:
    vocab_size: int = 512
    context_length: int = 128
    hidden_size: int = 128
    num_layers: int = 2
    num_heads: int = 4
    num_experts: int = 4
    experts_per_token: int = 2
    expert_intermediate_size: int = 256
    dropout: float = 0.0
    tie_embeddings: bool = True

    @classmethod
    def from_json(cls, path: str | Path) -> "ProtonMoEConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        model = data.get("model", data)
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value for key, value in model.items() if key in allowed})

    def validate(self) -> None:
        if self.vocab_size < 2 or self.context_length < 1:
            raise ValueError("vocab_size and context_length must be positive")
        if self.hidden_size < 8 or self.num_layers < 1:
            raise ValueError("hidden_size and num_layers must be positive")
        if self.hidden_size % self.num_heads:
            raise ValueError("hidden_size must be divisible by num_heads")
        if not 1 <= self.experts_per_token <= self.num_experts:
            raise ValueError("experts_per_token must be between 1 and num_experts")
        if self.num_experts < 1 or self.expert_intermediate_size < 1:
            raise ValueError("expert dimensions must be positive")


class RMSNorm(nn.Module):
    def __init__(self, width: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scale = torch.rsqrt(x.float().pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return (x * scale.to(dtype=x.dtype)) * self.weight


class SwiGLUExpert(nn.Module):
    def __init__(self, width: int, intermediate: int, dropout: float):
        super().__init__()
        self.gate = nn.Linear(width, intermediate, bias=False)
        self.up = nn.Linear(width, intermediate, bias=False)
        self.down = nn.Linear(intermediate, width, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.down(F.silu(self.gate(x)) * self.up(x)))


class TopKMoE(nn.Module):
    """Sparse top-k router; only selected experts process each token."""

    def __init__(self, width: int, intermediate: int, experts: int,
                 top_k: int, dropout: float = 0.0):
        super().__init__()
        if not 1 <= top_k <= experts:
            raise ValueError("top_k must be in [1, experts]")
        self.num_experts = experts
        self.top_k = top_k
        self.router = nn.Linear(width, experts, bias=False)
        self.experts = nn.ModuleList(
            SwiGLUExpert(width, intermediate, dropout) for _ in range(experts)
        )
        self.last_router_stats: dict[str, Any] = {}

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        original_shape = x.shape
        flat = x.reshape(-1, original_shape[-1])
        router_logits = self.router(flat).float()
        probabilities = F.softmax(router_logits, dim=-1)
        top_weights, top_indices = torch.topk(probabilities, self.top_k, dim=-1)
        top_weights = top_weights / top_weights.sum(dim=-1, keepdim=True).clamp_min(1e-9)

        combined = torch.zeros_like(flat)
        assignments = torch.zeros_like(probabilities)
        for expert_id, expert in enumerate(self.experts):
            token_rows, slots = torch.where(top_indices == expert_id)
            if token_rows.numel() == 0:
                continue
            expert_input = flat.index_select(0, token_rows)
            expert_output = expert(expert_input)
            weighted = expert_output * top_weights[token_rows, slots].to(expert_output.dtype).unsqueeze(-1)
            combined.index_add_(0, token_rows, weighted)
            assignments[token_rows, expert_id] = 1.0

        importance = probabilities.mean(dim=0)
        load = assignments.mean(dim=0)
        auxiliary_loss = self.num_experts * torch.sum(importance * load)
        with torch.no_grad():
            self.last_router_stats = {
                "tokens": int(flat.shape[0]),
                "experts": self.num_experts,
                "top_k": self.top_k,
                "tokens_per_expert": assignments.sum(dim=0).to(torch.int64).cpu().tolist(),
                "mean_router_probability": importance.cpu().tolist(),
            }
        return combined.reshape(original_shape), auxiliary_loss


class CausalSelfAttention(nn.Module):
    def __init__(self, width: int, heads: int, dropout: float):
        super().__init__()
        self.heads = heads
        self.head_dim = width // heads
        self.qkv = nn.Linear(width, 3 * width, bias=False)
        self.output = nn.Linear(width, width, bias=False)
        self.dropout = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, length, width = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        shape = (batch, length, self.heads, self.head_dim)
        q = q.view(shape).transpose(1, 2)
        k = k.view(shape).transpose(1, 2)
        v = v.view(shape).transpose(1, 2)
        attended = F.scaled_dot_product_attention(
            q, k, v, attn_mask=None, dropout_p=self.dropout if self.training else 0.0,
            is_causal=True,
        )
        attended = attended.transpose(1, 2).contiguous().view(batch, length, width)
        return self.output(attended)


class ProtonMoEBlock(nn.Module):
    def __init__(self, config: ProtonMoEConfig):
        super().__init__()
        self.attn_norm = RMSNorm(config.hidden_size)
        self.attention = CausalSelfAttention(
            config.hidden_size, config.num_heads, config.dropout
        )
        self.moe_norm = RMSNorm(config.hidden_size)
        self.moe = TopKMoE(
            config.hidden_size, config.expert_intermediate_size,
            config.num_experts, config.experts_per_token, config.dropout,
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = x + self.attention(self.attn_norm(x))
        moe_output, aux_loss = self.moe(self.moe_norm(x))
        return x + moe_output, aux_loss


class ProtonMoE(nn.Module):
    """Decoder-only language model. Returns logits and router diagnostics."""

    def __init__(self, config: ProtonMoEConfig):
        super().__init__()
        config.validate()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.hidden_size)
        self.position_embedding = nn.Embedding(config.context_length, config.hidden_size)
        self.blocks = nn.ModuleList(ProtonMoEBlock(config) for _ in range(config.num_layers))
        self.final_norm = RMSNorm(config.hidden_size)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        if config.tie_embeddings:
            self.lm_head.weight = self.token_embedding.weight

    def forward(self, token_ids: torch.Tensor) -> dict[str, Any]:
        if token_ids.ndim != 2:
            raise ValueError("token_ids must have shape [batch, sequence]")
        batch, length = token_ids.shape
        if length > self.config.context_length:
            raise ValueError("sequence exceeds configured context_length")
        positions = torch.arange(length, device=token_ids.device)
        x = self.token_embedding(token_ids) + self.position_embedding(positions)[None, :, :]
        auxiliary_losses = []
        router_stats = []
        for block in self.blocks:
            x, aux = block(x)
            auxiliary_losses.append(aux)
            router_stats.append(block.moe.last_router_stats)
        logits = self.lm_head(self.final_norm(x))
        aux_loss = torch.stack(auxiliary_losses).mean()
        return {"logits": logits, "aux_loss": aux_loss, "router_stats": router_stats}

    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def architecture_summary(self) -> dict[str, Any]:
        cfg = self.config
        return {
            "name": "Proton Brain MoE",
            "parameters": self.parameter_count(),
            "layers": cfg.num_layers,
            "experts": cfg.num_experts,
            "experts_per_token": cfg.experts_per_token,
            "hidden_size": cfg.hidden_size,
            "context_length": cfg.context_length,
            "vocab_size": cfg.vocab_size,
            "quantization": "not applied by this PyTorch research module",
        }

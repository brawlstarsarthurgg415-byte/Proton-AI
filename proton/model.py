"""A small decoder-only Transformer initialized from random weights."""
from __future__ import annotations

import torch
from torch import nn


class ProtonTransformer(nn.Module):
    def __init__(self, vocab_size: int, block_size: int = 128,
                 width: int = 128, heads: int = 4, layers: int = 4,
                 dropout: float = 0.1):
        super().__init__()
        if width % heads:
            raise ValueError("width must be divisible by heads")
        self.block_size = block_size
        self.token = nn.Embedding(vocab_size, width)
        self.position = nn.Embedding(block_size, width)
        layer = nn.TransformerEncoderLayer(
            d_model=width, nhead=heads, dim_feedforward=4 * width,
            dropout=dropout, batch_first=True, norm_first=True,
            activation="gelu",
        )
        self.blocks = nn.TransformerEncoder(layer, num_layers=layers)
        self.norm = nn.LayerNorm(width)
        self.output = nn.Linear(width, vocab_size, bias=False)
        self.output.weight = self.token.weight

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        batch, length = tokens.shape
        if length > self.block_size:
            raise ValueError(f"sequence length {length} exceeds {self.block_size}")
        positions = torch.arange(length, device=tokens.device)
        x = self.token(tokens) + self.position(positions)[None, :, :]
        # Causal mask prevents the model from seeing future characters.
        mask = torch.triu(torch.ones(length, length, device=tokens.device,
                                     dtype=torch.bool), diagonal=1)
        x = self.blocks(x, mask=mask)
        return self.output(self.norm(x))

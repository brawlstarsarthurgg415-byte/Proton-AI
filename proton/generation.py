"""Local text generation from Proton's evolved character-level checkpoint."""
from __future__ import annotations

from pathlib import Path

import torch

from .model import ProtonTransformer

ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT = ROOT / "checkpoints" / "proton-evolved.pt"


def generate_local_reply(message: str, checkpoint_path: Path = CHECKPOINT,
                         max_new_chars: int = 220) -> str | None:
    if not checkpoint_path.is_file():
        return None
    try:
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        stoi = checkpoint["stoi"]
        config = checkpoint["config"]
        itos = {index: char for char, index in stoi.items()}
        model = ProtonTransformer(**config)
        model.load_state_dict(checkpoint["model"])
        model.eval()
        prefix = f"Usuário: {message.strip()}\nProton:"
        # Unknown characters are omitted rather than mapped to a false token.
        encoded = [stoi[ch] for ch in prefix if ch in stoi]
        if not encoded:
            return None
        tokens = torch.tensor([encoded[-config["block_size"]:]], dtype=torch.long)
        output = []
        with torch.no_grad():
            for _ in range(max_new_chars):
                context = tokens[:, -config["block_size"]:]
                logits = model(context)[:, -1, :] / 0.85
                probabilities = torch.softmax(logits, dim=-1)
                next_token = torch.multinomial(probabilities, num_samples=1)
                token_id = int(next_token.item())
                char = itos.get(token_id, "")
                if char == "\n":
                    break
                output.append(char)
                tokens = torch.cat((tokens, next_token), dim=1)
        answer = "".join(output).strip()
        if not answer:
            return "Ainda estou aprendendo a formular respostas. Pode tentar perguntar de outro jeito?"
        return answer
    except (OSError, ValueError, KeyError, RuntimeError, TypeError):
        return None

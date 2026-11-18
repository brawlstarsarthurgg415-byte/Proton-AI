"""Train Proton from scratch on a local UTF-8 text file."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from .model import ProtonTransformer

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "starter.txt"
DEFAULT_OUT = ROOT / "checkpoints"


def load_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")
    text = path.read_text(encoding="utf-8")
    if len(text) < 100:
        raise ValueError("Dataset must contain at least 100 characters.")
    return text


def train(hours: float, data_path: Path, out_dir: Path,
          max_steps: int = 0, device_name: str = "auto") -> Path:
    if hours <= 0 or hours > 24:
        raise ValueError("hours must be greater than 0 and no more than 24")
    text = load_text(data_path)
    chars = sorted(set(text))
    stoi = {ch: i for i, ch in enumerate(chars)}
    encoded = torch.tensor([stoi[ch] for ch in text], dtype=torch.long)
    if len(encoded) < 4:
        raise ValueError("Not enough training tokens")
    device = ("cuda" if torch.cuda.is_available() else "cpu") if device_name == "auto" else device_name
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    torch.manual_seed(42)
    model = ProtonTransformer(len(chars)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    block = model.block_size
    deadline = time.monotonic() + hours * 3600
    step = 0
    last_loss = None
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Training from random weights | device={device} | chars={len(chars)}")
    print("This starter corpus is for pipeline testing, not broad knowledge acquisition.")
    while time.monotonic() < deadline and (max_steps <= 0 or step < max_steps):
        starts = torch.randint(0, len(encoded) - 1, (16,))
        starts = starts.clamp(max=max(0, len(encoded) - block - 1))
        batch = torch.stack([encoded[int(i):int(i) + block + 1] for i in starts])
        x, y = batch[:, :-1].to(device), batch[:, 1:].to(device)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, len(chars)), y.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        step += 1
        last_loss = float(loss.detach().cpu())
        if step % 50 == 0:
            print(f"step={step} loss={last_loss:.4f}")
        if step % 200 == 0:
            save_checkpoint(out_dir, model, stoi, step, last_loss)
    path = save_checkpoint(out_dir, model, stoi, step, last_loss)
    print(f"Finished: steps={step}, loss={last_loss}, checkpoint={path}")
    return path


def save_checkpoint(out_dir: Path, model: ProtonTransformer, stoi: dict,
                    step: int, loss: float | None) -> Path:
    path = out_dir / "proton-latest.pt"
    temp = out_dir / "proton-latest.tmp"
    torch.save({"model": model.state_dict(), "stoi": stoi,
                "config": {"vocab_size": len(stoi), "block_size": model.block_size,
                           "width": 128, "heads": 4, "layers": 4},
                "step": step, "loss": loss}, temp)
    temp.replace(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the Proton neural core from scratch.")
    parser.add_argument("--hours", type=float, default=0.05, help="maximum runtime in hours (default: 3 minutes)")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-steps", type=int, default=0, help="optional step limit; 0 means time limit only")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args()
    train(args.hours, args.data, args.output, args.max_steps, args.device)


if __name__ == "__main__":
    main()

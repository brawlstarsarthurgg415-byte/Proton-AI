"""Train and evaluate Proton's small decoder-only model on a local text corpus.

This is an educational prototype, not a production-scale language model.
"""
from __future__ import annotations

import argparse
import random
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
    if len(text.strip()) < 100:
        raise ValueError("Dataset must contain at least 100 non-whitespace characters.")
    if len(set(text)) < 8:
        raise ValueError("Dataset has too few distinct characters.")
    return text


def encode_corpus(text: str):
    # Character-level vocabulary keeps this first implementation dependency-free.
    chars = sorted(set(text))
    stoi = {char: index for index, char in enumerate(chars)}
    encoded = torch.tensor([stoi[char] for char in text], dtype=torch.long)
    if len(encoded) < 40:
        raise ValueError("Corpus is too short for a train/validation split.")
    split = max(1, min(len(encoded) - 1, int(len(encoded) * 0.9)))
    return chars, stoi, encoded[:split], encoded[split:]


def sample_batch(data: torch.Tensor, batch_size: int, block_size: int, device: str):
    if len(data) <= block_size:
        raise ValueError("Training split must be longer than the context window.")
    starts = torch.randint(0, len(data) - block_size, (batch_size,))
    batch = torch.stack([data[int(start):int(start) + block_size + 1] for start in starts])
    return batch[:, :-1].to(device), batch[:, 1:].to(device)


@torch.no_grad()
def estimate_loss(model, train_data, val_data, block_size, batch_size, device, batches=8):
    model.eval()
    result = {}
    for name, data in (("train", train_data), ("validation", val_data)):
        if len(data) <= block_size:
            result[name] = None
            continue
        losses = []
        for _ in range(batches):
            x, y = sample_batch(data, batch_size, block_size, device)
            logits = model(x)
            losses.append(F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1)).item())
        result[name] = sum(losses) / len(losses)
    model.train()
    return result


def save_checkpoint(out_dir, model, optimizer, stoi, config, step, metrics):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "proton-latest.pt"
    temporary = out_dir / "proton-latest.tmp"
    payload = {
        "format_version": 2,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "stoi": stoi,
        "config": config,
        "step": step,
        "metrics": metrics,
        "torch_rng_state": torch.get_rng_state(),
        "python_rng_state": random.getstate(),
    }
    torch.save(payload, temporary)
    temporary.replace(path)
    return path


def train(hours: float, data_path: Path, out_dir: Path, max_steps: int = 500,
          device_name: str = "auto", resume: bool = False, block_size: int = 64,
          width: int = 64, layers: int = 2, heads: int = 4,
          batch_size: int = 8, eval_interval: int = 50) -> Path:
    if hours <= 0 or hours > 24:
        raise ValueError("hours must be greater than 0 and no more than 24")
    if max_steps < 1 or block_size < 8 or width < 8 or layers < 1 or heads < 1 or batch_size < 1:
        raise ValueError("Model sizes, batch size, and max_steps must be positive and sensible.")
    if width % heads:
        raise ValueError("width must be divisible by heads")

    text = load_text(data_path)
    chars, stoi, train_data, val_data = encode_corpus(text)
    # Keep the model context within the amount of text actually available.
    block_size = min(block_size, max(8, len(train_data) - 1))
    device = ("cuda" if torch.cuda.is_available() else "cpu") if device_name == "auto" else device_name
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    torch.manual_seed(42)
    random.seed(42)

    config = {"vocab_size": len(chars), "block_size": block_size, "width": width,
              "heads": heads, "layers": layers, "dropout": 0.1}
    model = ProtonTransformer(**config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    step = 0
    metrics = {"train": None, "validation": None}

    checkpoint_path = out_dir / "proton-latest.pt"
    if resume and checkpoint_path.is_file():
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
        if checkpoint.get("stoi") != stoi or checkpoint.get("config") != config:
            raise ValueError("Checkpoint vocabulary/config does not match this corpus or model settings.")
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        step = int(checkpoint.get("step", 0))
        metrics = checkpoint.get("metrics", metrics)
        if checkpoint.get("torch_rng_state") is not None:
            torch.set_rng_state(checkpoint["torch_rng_state"].cpu())
        if checkpoint.get("python_rng_state") is not None:
            random.setstate(checkpoint["python_rng_state"])
        print(f"Checkpoint resumed at step {step}.")

    deadline = time.monotonic() + hours * 3600
    target_step = step + max_steps
    model.train()
    print(f"Proton neural training | device={device} | vocab={len(chars)} | train_chars={len(train_data)} | validation_chars={len(val_data)}")
    print("This small character model is experimental; training loss is not proof of understanding.")
    while time.monotonic() < deadline and step < target_step:
        x, y = sample_batch(train_data, batch_size, block_size, device)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, len(chars)), y.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        step += 1

        if step % eval_interval == 0 or step == target_step:
            metrics = estimate_loss(model, train_data, val_data, block_size, batch_size, device)
            print(f"step={step} train_loss={metrics['train']:.4f} validation_loss={metrics['validation'] if metrics['validation'] is not None else 'n/a'}")
            save_checkpoint(out_dir, model, optimizer, stoi, config, step, metrics)

    path = save_checkpoint(out_dir, model, optimizer, stoi, config, step, metrics)
    print(f"Checkpoint saved: {path} (step={step})")
    print("Next milestone: larger reviewed datasets and independent capability evaluations.")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Proton's experimental neural core.")
    parser.add_argument("--hours", type=float, default=0.02, help="runtime limit in hours (default: about 72 seconds)")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-steps", type=int, default=500, help="maximum new optimizer steps")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--resume", action="store_true", help="resume a compatible local checkpoint")
    parser.add_argument("--block-size", type=int, default=64)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--eval-interval", type=int, default=50)
    args = parser.parse_args()
    train(args.hours, args.data, args.output, args.max_steps, args.device,
          args.resume, args.block_size, args.width, args.layers, args.heads,
          args.batch_size, args.eval_interval)


if __name__ == "__main__":
    main()

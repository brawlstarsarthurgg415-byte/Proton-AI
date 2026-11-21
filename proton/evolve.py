"""Five-minute Lamarckian neuroevolution for Proton's local language model.

Each individual is a small Transformer. Candidates learn from the corpus with
a few gradient steps, are scored on held-out text, and the strongest survive.
Children inherit weights and receive controlled Gaussian mutations.
"""
from __future__ import annotations

import argparse
import copy
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from .model import ProtonTransformer

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "conversation-pt.txt"
DEFAULT_OUT = ROOT / "checkpoints"


def load_corpus(path: Path):
    text = path.read_text(encoding="utf-8")
    if len(text.strip()) < 300:
        raise ValueError("O corpus precisa ter pelo menos 300 caracteres úteis.")
    chars = sorted(set(text))
    stoi = {ch: i for i, ch in enumerate(chars)}
    ids = torch.tensor([stoi[ch] for ch in text], dtype=torch.long)
    split = int(len(ids) * 0.9)
    if split < 80 or len(ids) - split < 16:
        raise ValueError("Corpus insuficiente para treino e validação.")
    return chars, stoi, ids[:split], ids[split:]


def batch(data, size, context, device):
    if len(data) <= context + 1:
        raise ValueError("Poucos dados para o contexto de treinamento.")
    starts = torch.randint(0, len(data) - context - 1, (size,))
    chunks = torch.stack([data[int(i):int(i) + context + 1] for i in starts])
    return chunks[:, :-1].to(device), chunks[:, 1:].to(device)


@torch.no_grad()
def score(model, data, context, device, rounds=3):
    model.eval()
    values = []
    for _ in range(rounds):
        x, y = batch(data, 4, context, device)
        logits = model(x)
        values.append(F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1)).item())
    model.train()
    return sum(values) / len(values)


def train_candidate(model, train_data, context, device, steps, deadline):
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)
    done = 0
    while done < steps and time.monotonic() < deadline:
        x, y = batch(train_data, 4, context, device)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        done += 1
    return done


def mutate(parent, scale):
    child = ProtonTransformer(vocab_size=parent.token.num_embeddings,
                              block_size=parent.block_size, width=32,
                              heads=2, layers=1, dropout=0.0)
    child.load_state_dict(copy.deepcopy(parent.state_dict()))
    with torch.no_grad():
        for parameter in child.parameters():
            if parameter.is_floating_point():
                parameter.add_(torch.randn_like(parameter) * scale)
    return child


def save_best(out_dir, model, stoi, config, metrics):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "proton-evolved.pt"
    temp = out_dir / "proton-evolved.tmp"
    torch.save({
        "format_version": 1,
        "model": model.state_dict(),
        "stoi": stoi,
        "config": config,
        "metrics": metrics,
        "kind": "neuroevolution",
    }, temp)
    temp.replace(path)
    return path


def evolve(minutes=5.0, data_path=DEFAULT_DATA, out_dir=DEFAULT_OUT,
           population_size=4, elite_count=2, steps_per_candidate=8,
           device_name="auto", seed=17):
    if not 0.1 <= minutes <= 30:
        raise ValueError("A duração deve ficar entre 0,1 e 30 minutos.")
    if population_size < 2 or not 1 <= elite_count < population_size:
        raise ValueError("A população precisa ter pelo menos 2 indivíduos e elites válidas.")
    random.seed(seed)
    torch.manual_seed(seed)
    if device_name == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = device_name
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA não está disponível neste aparelho.")
    if device == "cpu":
        torch.set_num_threads(max(1, min(2, torch.get_num_threads())))

    chars, stoi, train_data, val_data = load_corpus(data_path)
    config = {"vocab_size": len(chars), "block_size": 64, "width": 32,
              "heads": 2, "layers": 1, "dropout": 0.0}
    deadline = time.monotonic() + minutes * 60
    population = [ProtonTransformer(**config).to(device) for _ in range(population_size)]
    best_loss = float("inf")
    best_model = None
    generation = 0
    print(f"PROTON NEUROEVOLUTION | {minutes:.1f} min | device={device}")
    print(f"População: {population_size} | elites: {elite_count} | parâmetros por rede: {sum(p.numel() for p in population[0].parameters()):,}")
    print("Currículo: contexto começa em 16 caracteres e aumenta até 64.")
    while time.monotonic() < deadline:
        generation += 1
        context = min(64, 16 + (generation - 1) * 8)
        ranked = []
        for index, model in enumerate(population):
            if time.monotonic() >= deadline:
                break
            steps = train_candidate(model, train_data, context, device,
                                    steps_per_candidate, deadline)
            if steps == 0:
                break
            loss = score(model, val_data, context, device)
            ranked.append((loss, model))
            if loss < best_loss:
                best_loss = loss
                best_model = copy.deepcopy(model).cpu()
                metrics = {"validation_loss": best_loss, "generation": generation,
                           "context": context, "device": device}
                path = save_best(out_dir, best_model, stoi, config, metrics)
                print(f"Novo recorde | geração={generation} | indivíduo={index + 1} | validação={loss:.4f} | salvo={path}")
        if not ranked or time.monotonic() >= deadline:
            break
        ranked.sort(key=lambda item: item[0])
        print(f"Geração {generation}: melhor validação={ranked[0][0]:.4f} | contexto={context}")
        survivors = [item[1] for item in ranked[:elite_count]]
        next_population = [copy.deepcopy(model) for model in survivors]
        while len(next_population) < population_size:
            parent = random.choice(survivors)
            scale = random.choice((0.002, 0.005, 0.01, 0.02))
            next_population.append(mutate(parent, scale))
        population = next_population
    if best_model is None:
        raise RuntimeError("O tempo terminou antes de concluir uma avaliação.")
    final_path = save_best(out_dir, best_model, stoi, config,
                           {"validation_loss": best_loss, "generation": generation,
                            "device": device})
    print(f"Treinamento encerrado após {minutes:.1f} minutos.")
    print(f"Melhor indivíduo: geração {generation} | perda de validação {best_loss:.4f}")
    print(f"Modelo salvo em: {final_path}")
    print("Nota: perda menor indica melhor previsão dos caracteres do corpus, não compreensão humana.")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="Neuroevolução local do Proton.")
    parser.add_argument("--minutes", type=float, default=5.0)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--population", type=int, default=4)
    parser.add_argument("--elites", type=int, default=2)
    parser.add_argument("--steps-per-candidate", type=int, default=8)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args()
    evolve(args.minutes, args.data, args.output, args.population, args.elites,
           args.steps_per_candidate, args.device)


if __name__ == "__main__":
    main()

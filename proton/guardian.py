"""Optional local Qwen3Guard safety screening for collective proposals.

A model verdict is advisory: it never approves content or makes it training-eligible.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_ID = "Qwen/Qwen3Guard-Gen-0.6B"
LABEL_RE = re.compile(r"Safety:\\s*(Safe|Unsafe|Controversial)", re.IGNORECASE)
CATEGORY_RE = re.compile(
    r"(Violent|Non-violent Illegal Acts|Sexual Content or Sexual Acts|PII|"
    r"Suicide & Self-Harm|Unethical Acts|Politically Sensitive Topics|"
    r"Copyright Violation|Jailbreak|None)",
    re.IGNORECASE,
)


class GuardianError(RuntimeError):
    pass


def parse_verdict(output: str) -> dict[str, Any]:
    match = LABEL_RE.search(output)
    categories = CATEGORY_RE.findall(output)
    if not match:
        return {
            "verdict": "unknown",
            "categories": categories,
            "recommendation": "quarantine",
            "raw_output": output[:2000],
        }
    verdict = match.group(1).capitalize()
    return {
        "verdict": verdict.lower(),
        "categories": categories,
        "recommendation": "manual_review" if verdict == "Safe" else "quarantine",
        "raw_output": output[:2000],
    }


def _load_model(model_id: str):
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise GuardianError(
            "Instale as dependências opcionais: pip install -e '.[guardian]'"
        ) from exc
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype="auto", device_map="auto"
        )
    except Exception as exc:
        raise GuardianError(f"Não foi possível carregar {model_id}: {exc}") from exc
    return torch, tokenizer, model


def _classify(content: str, torch, tokenizer, model) -> dict[str, Any]:
    messages = [{"role": "user", "content": content[:12000]}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False)
    inputs = tokenizer([prompt], return_tensors="pt").to(model.device)
    with torch.inference_mode():
        generated = model.generate(**inputs, max_new_tokens=128)
    new_tokens = generated[0][len(inputs.input_ids[0]):]
    output = tokenizer.decode(new_tokens, skip_special_tokens=True)
    result = parse_verdict(output)
    result["model"] = MODEL_ID
    result["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    return result


def review_text(content: str, model_id: str = MODEL_ID) -> dict[str, Any]:
    """Run Qwen3Guard locally via Transformers; weights download on first use."""
    torch, tokenizer, model = _load_model(model_id)
    try:
        result = _classify(content, torch, tokenizer, model)
        result["model"] = model_id
        return result
    except Exception as exc:
        raise GuardianError(f"Falha ao executar {model_id}: {exc}") from exc


def review_outbox(outbox: Path, *, limit: int = 20,
                  model_id: str = MODEL_ID) -> list[dict[str, Any]]:
    """Screen queued proposals once per run; never approve or export them."""
    if limit < 1:
        raise GuardianError("limit deve ser maior que zero")
    candidates = []
    if outbox.exists():
        for path in sorted(outbox.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (isinstance(record, dict)
                    and record.get("schema") == "proton-lesson-v1"
                    and not record.get("guardian_review")):
                candidates.append((path, record))
            if len(candidates) >= limit:
                break
    if not candidates:
        return []

    torch, tokenizer, model = _load_model(model_id)
    reviewed = []
    for path, record in candidates:
        try:
            result = _classify(str(record.get("content", "")), torch, tokenizer, model)
            result["model"] = model_id
        except Exception as exc:
            raise GuardianError(f"Falha ao analisar {path.name}: {exc}") from exc
        record["guardian_review"] = result
        # Screening is not curation: preserve status and training_eligible unchanged.
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\\n",
                        encoding="utf-8")
        reviewed.append({"id": record.get("id", path.stem), **result})
    return reviewed

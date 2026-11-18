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
LABEL_RE = re.compile(r"Safety:\s*(Safe|Unsafe|Controversial)", re.IGNORECASE)
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
    recommendation = "manual_review" if verdict == "Safe" else "quarantine"
    return {
        "verdict": verdict.lower(),
        "categories": categories,
        "recommendation": recommendation,
        "raw_output": output[:2000],
    }


def review_text(content: str, model_id: str = MODEL_ID) -> dict[str, Any]:
    """Run Qwen3Guard locally via Transformers; model weights download on first use."""
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
        messages = [{"role": "user", "content": content[:12000]}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False)
        inputs = tokenizer([prompt], return_tensors="pt").to(model.device)
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=128)
        new_tokens = generated[0][len(inputs.input_ids[0]):]
        output = tokenizer.decode(new_tokens, skip_special_tokens=True)
    except Exception as exc:
        raise GuardianError(f"Falha ao executar {model_id}: {exc}") from exc

    result = parse_verdict(output)
    result["model"] = model_id
    result["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    return result


def review_outbox(outbox: Path, *, limit: int = 20,
                  model_id: str = MODEL_ID) -> list[dict[str, Any]]:
    """Screen queued proposals; never approve or export them."""
    if limit < 1:
        raise GuardianError("limit deve ser maior que zero")
    reviewed = []
    candidates = sorted(outbox.glob("*.json"))[:limit] if outbox.exists() else []
    for path in candidates:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict) or record.get("schema") != "proton-lesson-v1":
            continue
        result = review_text(str(record.get("content", "")), model_id=model_id)
        record["guardian_review"] = result
        # Screening is not curation: preserve status and training_eligible unchanged.
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        reviewed.append({"id": record.get("id", path.stem), **result})
    return reviewed

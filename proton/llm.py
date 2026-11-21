"""OpenAI-compatible chat completion adapter for Proton-AI.

Configure PROTON_LLM_API_KEY, PROTON_LLM_MODEL and optionally
PROTON_LLM_BASE_URL on the hosting service. No provider key is bundled.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def generate_chat_reply(history: list[dict[str, str]], message: str) -> str | None:
    api_key = os.environ.get("PROTON_LLM_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = os.environ.get("PROTON_LLM_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    model = os.environ.get("PROTON_LLM_MODEL", "gpt-4o-mini").strip()
    if not base_url or not model:
        return None

    messages = [{
        "role": "system",
        "content": (
            "Você é Proton, um assistente conversacional em português brasileiro. "
            "Converse de forma natural, clara e amigável, como uma pessoa educada: "
            "responda ao que foi dito, acompanhe o contexto, faça perguntas relevantes "
            "quando necessário e evite repetir bordões ou respostas genéricas. "
            "Não invente fatos, capacidades, memórias ou ações. Se não souber, diga. "
            "Use respostas proporcionais à pergunta e explique assuntos difíceis por etapas."
        ),
    }]
    messages.extend(history[-12:])
    messages.append({"role": "user", "content": message})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
    }).encode("utf-8")
    request = Request(
        base_url + "/chat/completions",
        data=body,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data["choices"][0]["message"]["content"]
        if isinstance(answer, str) and answer.strip():
            return answer.strip()[:12000]
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError, OSError):
        return None
    return None

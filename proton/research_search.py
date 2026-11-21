"""Local search over Proton's source-attributed research library.

This is retrieval, not neural understanding: results remain unverified references
and are always shown with their original source URL.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LIBRARY = ROOT / "data" / "research-library.jsonl"
TOKEN_RE = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)
STOP_WORDS = {
    "a", "à", "as", "ao", "aos", "aquela", "aquele", "aquilo", "com",
    "como", "da", "das", "de", "dela", "dele", "do", "dos", "e", "é",
    "em", "entre", "era", "essa", "esse", "esta", "este", "eu", "foi",
    "há", "isso", "isto", "mais", "mas", "me", "minha", "muito", "na",
    "nas", "no", "nos", "o", "os", "ou", "para", "pela", "pelas", "pelo",
    "pelos", "por", "qual", "quando", "que", "quem", "se", "sem", "ser",
    "seu", "sua", "também", "tem", "um", "uma", "você",
}


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in value if not unicodedata.combining(char))


def _tokens(value: str) -> list[str]:
    return [
        token for token in TOKEN_RE.findall(_normalize(value))
        if len(token) > 1 and token not in STOP_WORDS
    ]


def load_research_records(path: str | Path = DEFAULT_LIBRARY) -> list[dict[str, Any]]:
    """Read valid JSONL records, skipping malformed lines without crashing."""
    library = Path(path)
    if not library.is_file():
        return []
    records: list[dict[str, Any]] = []
    try:
        with library.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    isinstance(item, dict)
                    and isinstance(item.get("extract"), str)
                    and item.get("extract").strip()
                    and isinstance(item.get("url"), str)
                    and item.get("url").startswith(("https://", "http://"))
                ):
                    records.append(item)
    except OSError:
        return []
    return records


def search_research_library(
    query: str, *, path: str | Path = DEFAULT_LIBRARY, limit: int = 3
) -> list[dict[str, Any]]:
    """Rank library pages by a small TF-IDF-like lexical relevance score."""
    if not 1 <= limit <= 10:
        raise ValueError("O limite deve ficar entre 1 e 10.")
    query_terms = _tokens(query)
    if not query_terms:
        return []
    records = load_research_records(path)
    if not records:
        return []

    query_counts = Counter(query_terms)
    documents: list[tuple[dict[str, Any], Counter[str], int]] = []
    document_frequency: Counter[str] = Counter()
    for record in records:
        title = str(record.get("title", ""))
        topic = str(record.get("topic", ""))
        extract = str(record.get("extract", ""))
        terms = _tokens(title + " " + topic + " " + extract)
        counts = Counter(terms)
        documents.append((record, counts, max(1, sum(counts.values()))))
        document_frequency.update(set(counts))

    total = len(documents)
    ranked: list[tuple[float, dict[str, Any]]] = []
    for record, counts, length in documents:
        score = 0.0
        matched = 0
        for term, query_count in query_counts.items():
            frequency = counts.get(term, 0)
            if not frequency:
                continue
            matched += 1
            inverse_frequency = math.log(1 + (total - document_frequency[term] + 0.5)
                                          / (document_frequency[term] + 0.5))
            # Title/topic matches count more than body matches.
            title_terms = set(_tokens(str(record.get("title", "")) + " "
                                      + str(record.get("topic", ""))))
            title_boost = 2.5 if term in title_terms else 1.0
            score += query_count * inverse_frequency * title_boost * (
                frequency / (frequency + 1.2 * (0.25 + 0.75 * length / 500))
            )
        if matched:
            score *= matched / len(query_counts)
            ranked.append((score, {**record, "relevance_score": round(score, 4)}))

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [record for score, record in ranked[:limit] if score > 0]


def format_research_results(results: list[dict[str, Any]]) -> str:
    """Format references transparently; never present them as verified answers."""
    if not results:
        return "Não encontrei páginas relacionadas na biblioteca de pesquisas."
    lines = [
        "Encontrei estas referências na biblioteca local do Proton:",
        "Atenção: são trechos de referência ainda não verificados, não respostas garantidas.",
    ]
    for index, item in enumerate(results, 1):
        title = str(item.get("title") or "Página sem título").strip()
        topic = str(item.get("topic") or "tema não registrado").strip()
        extract = re.sub(r"\s+", " ", str(item.get("extract", ""))).strip()
        if len(extract) > 850:
            extract = extract[:847].rsplit(" ", 1)[0] + "..."
        lines.extend([
            "",
            f"{index}. {title} (tema: {topic})",
            extract,
            f"Fonte: {item.get('url')}",
        ])
    lines.extend(["", "Use /ask com termos mais específicos para refinar a busca."])
    return "\n".join(lines)

"""Autonomous, source-attributed research for Proton (Wikipedia phase 1).

Downloaded text is untrusted reference material, not verified truth and not
automatically neural-training data. Only public MediaWiki API endpoints are used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = ROOT / "data" / "research-queue.json"
LIBRARY_PATH = ROOT / "data" / "research-library.jsonl"
API_URL = "https://pt.wikipedia.org/w/api.php"
USER_AGENT = "Proton-AI-Research/0.1 (educational open-source project)"
DEFAULT_TOPICS = [
    "fundamentos de programação", "matemática básica", "método científico",
    "física clássica", "biologia celular", "história do Brasil",
    "geografia física", "astronomia", "redes de computadores",
    "segurança digital", "língua portuguesa", "pensamento crítico",
]


class ResearchError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _request(params: dict[str, str], timeout: int = 20) -> dict[str, Any]:
    url = API_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ResearchError("Resposta da fonte excedeu o limite de 2 MB.")
        return json.loads(raw.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ResearchError(f"Falha ao consultar a Wikipedia ({exc.__class__.__name__}).") from exc


def load_queue(path: Path = QUEUE_PATH) -> list[dict[str, Any]]:
    queue = _read_json(path, None)
    if not isinstance(queue, list):
        queue = [{"topic": topic, "status": "pending", "priority": 50, "reason": "currículo inicial"}
                 for topic in DEFAULT_TOPICS]
        _write_json(path, queue)
    return queue


def add_topic(topic: str, *, reason: str = "adicionado pelo usuário",
              priority: int = 50, path: Path = QUEUE_PATH) -> bool:
    clean = " ".join(topic.split())
    if not clean or len(clean) > 160:
        raise ValueError("O tema deve ter entre 1 e 160 caracteres.")
    if not 1 <= priority <= 100:
        raise ValueError("A prioridade deve ficar entre 1 e 100.")
    queue = load_queue(path)
    if any(item.get("topic", "").casefold() == clean.casefold() for item in queue):
        return False
    queue.append({"topic": clean, "status": "pending", "priority": priority,
                  "reason": reason[:240], "added_at": _now()})
    _write_json(path, queue)
    return True


def record_gap(topic: str, score: float, *, path: Path = QUEUE_PATH) -> bool:
    """Queue a topic after a quiz/evaluation score indicates weak mastery."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("A pontuação deve estar entre 0 e 1.")
    if score >= 0.8:
        return False
    return add_topic(topic, reason=f"lacuna detectada em avaliação: {score:.0%}",
                     priority=max(1, min(100, round((1.0 - score) * 100))), path=path)


def search_wikipedia(topic: str, limit: int = 3) -> list[dict[str, Any]]:
    if not 1 <= limit <= 5:
        raise ValueError("O limite de páginas deve ficar entre 1 e 5.")
    data = _request({
        "action": "query", "list": "search", "srsearch": topic,
        "srnamespace": "0", "srlimit": str(limit), "format": "json",
        "utf8": "1", "formatversion": "2",
    })
    hits = data.get("query", {}).get("search", [])
    if not isinstance(hits, list):
        return []
    page_ids = [str(item.get("pageid")) for item in hits if item.get("pageid")]
    if not page_ids:
        return []
    details = _request({
        "action": "query", "pageids": "|".join(page_ids),
        "prop": "extracts|info|revisions", "explaintext": "1",
        "exintro": "1", "exchars": "3500", "inprop": "url",
        "rvprop": "ids", "format": "json", "utf8": "1",
        "formatversion": "2",
    })
    pages = details.get("query", {}).get("pages", [])
    by_id = {str(page.get("pageid")): page for page in pages if isinstance(page, dict)}
    results = []
    for hit in hits:
        page = by_id.get(str(hit.get("pageid")), {})
        extract = re.sub(r"\s+", " ", unescape(str(page.get("extract", "")))).strip()
        if len(extract) < 80:
            continue
        results.append({
            "pageid": page.get("pageid"),
            "title": page.get("title", hit.get("title", "")),
            "url": page.get("fullurl") or "https://pt.wikipedia.org/?curid=" + str(page.get("pageid")),
            "revision_id": (page.get("revisions") or [{}])[0].get("revid"),
            "extract": extract[:3500],
        })
    return results


def _known_keys(path: Path) -> set[str]:
    keys = set()
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
            keys.add(str(item.get("pageid")) + ":" + str(item.get("revision_id")))
        except (json.JSONDecodeError, AttributeError):
            continue
    return keys


def research_pending(*, max_topics: int = 3, pages_per_topic: int = 3,
                     queue_path: Path = QUEUE_PATH,
                     library_path: Path = LIBRARY_PATH,
                     pause_seconds: float = 1.0) -> dict[str, int]:
    if not 1 <= max_topics <= 10:
        raise ValueError("max_topics deve ficar entre 1 e 10.")
    queue = load_queue(queue_path)
    pending = sorted(
        (item for item in queue if item.get("status") == "pending"),
        key=lambda item: int(item.get("priority", 50)), reverse=True,
    )[:max_topics]
    known = _known_keys(library_path)
    library_path.parent.mkdir(parents=True, exist_ok=True)
    added = skipped = failed = 0
    for item in pending:
        topic = str(item.get("topic", "")).strip()
        if not topic:
            item["status"] = "invalid"
            continue
        try:
            pages = search_wikipedia(topic, pages_per_topic)
            if not pages:
                item["status"] = "no_results"
                item["last_checked_at"] = _now()
                skipped += 1
                continue
            with library_path.open("a", encoding="utf-8") as output:
                for page in pages:
                    key = str(page["pageid"]) + ":" + str(page.get("revision_id"))
                    if key in known:
                        skipped += 1
                        continue
                    record = {
                        "schema": "proton-research-v1",
                        "topic": topic,
                        **page,
                        "source_name": "Wikipedia em português",
                        "license": "CC BY-SA; preserve attribution and verify current terms",
                        "retrieved_at": _now(),
                        "content_sha256": hashlib.sha256(page["extract"].encode("utf-8")).hexdigest(),
                        "trust_status": "unverified_reference",
                        "training_eligible": False,
                    }
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    known.add(key)
                    added += 1
            item["status"] = "researched"
            item["last_checked_at"] = _now()
            item["pages_found"] = len(pages)
        except (ResearchError, OSError, ValueError) as exc:
            item["status"] = "pending"
            item["last_error"] = str(exc)[:240]
            failed += 1
        if pause_seconds:
            time.sleep(pause_seconds)
    _write_json(queue_path, queue)
    return {"topics_processed": len(pending), "pages_added": added,
            "duplicates_or_empty": skipped, "failures": failed}


def status(queue_path: Path = QUEUE_PATH, library_path: Path = LIBRARY_PATH) -> dict[str, int]:
    queue = load_queue(queue_path)
    counts = {"pending_topics": 0, "researched_topics": 0, "library_pages": 0}
    for item in queue:
        if item.get("status") == "pending":
            counts["pending_topics"] += 1
        elif item.get("status") == "researched":
            counts["researched_topics"] += 1
    if library_path.exists():
        counts["library_pages"] = sum(1 for line in library_path.read_text(encoding="utf-8").splitlines() if line.strip())
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(prog="proton-research")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="adicionar tema à fila de pesquisa")
    add.add_argument("topic")
    gap = sub.add_parser("gap", help="registrar assunto com baixo domínio (nota de 0 a 1)")
    gap.add_argument("topic")
    gap.add_argument("--score", type=float, required=True)
    run = sub.add_parser("run", help="pesquisar os próximos temas pendentes")
    run.add_argument("--max-topics", type=int, default=3)
    run.add_argument("--pages", type=int, default=3)
    sub.add_parser("status", help="mostrar estado da pesquisa")
    args = parser.parse_args()
    try:
        if args.command == "add":
            print("Tema adicionado." if add_topic(args.topic) else "Esse tema já está na fila.")
        elif args.command == "gap":
            added = record_gap(args.topic, args.score)
            print("Lacuna adicionada à fila." if added else "Nota suficiente ou tema já cadastrado.")
        elif args.command == "run":
            print(json.dumps(research_pending(max_topics=args.max_topics, pages_per_topic=args.pages),
                             ensure_ascii=False, indent=2))
        elif args.command == "status":
            print(json.dumps(status(), ensure_ascii=False, indent=2))
    except (ResearchError, ValueError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()

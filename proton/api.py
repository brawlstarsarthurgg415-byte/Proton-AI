"""Proton-AI API: conversational chat and reviewed knowledge intake."""
from __future__ import annotations

import hashlib
import os
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel, Field

from .llm import generate_chat_reply
from .personality import BrazilianPersonality

DATABASE_URL = os.environ.get("DATABASE_URL")
chat_sessions: dict[str, BrazilianPersonality] = {}
conversation_histories: dict[str, list[dict[str, str]]] = {}


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, connect_timeout=10)


class KnowledgeInput(BaseModel):
    content: str = Field(min_length=1, max_length=20000)
    kind: str = Field(default="lesson", pattern="^(lesson|correction|reference|ownership_claim)$")
    source_label: str | None = Field(default=None, max_length=500)
    sources: list[str] = Field(default_factory=list, max_length=10)


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, min_length=1, max_length=100)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Proton-AI conversational API", version="0.4.0", lifespan=lifespan)


def answer_message(session_id: str, message: str) -> tuple[str, str]:
    history = conversation_histories.setdefault(session_id, [])
    answer = generate_chat_reply(history, message)
    if answer:
        history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer},
        ])
        del history[:-24]
        return answer, "generative"

    # Honest fallback while a model provider is not configured.
    personality = chat_sessions.setdefault(session_id, BrazilianPersonality())
    return personality.reply(message), "basic"


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "chat_engine": "generative" if os.environ.get("PROTON_LLM_API_KEY") else "basic",
    }


@app.post("/chat")
def chat(payload: ChatInput):
    """Public conversational endpoint for the simple Proton chat page."""
    session_id = payload.session_id or str(uuid4())
    if len(conversation_histories) + len(chat_sessions) > 2000:
        conversation_histories.clear()
        chat_sessions.clear()
    reply, engine = answer_message(session_id, payload.message)
    return {"session_id": session_id, "reply": reply, "engine": engine}


@app.post("/app/chat")
def app_chat(payload: ChatInput):
    """Compatibility alias for older clients; no CEO panel is required."""
    return chat(payload)


@app.post("/knowledge", status_code=201)
def submit_knowledge(payload: KnowledgeInput, authorization: str | None = Header(default=None)):
    expected = os.environ.get("PROTON_API_KEY")
    if not expected or authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if payload.kind in {"lesson", "correction", "reference"} and not payload.sources:
        raise HTTPException(status_code=422, detail="At least one source URL is required")
    if any(not url.startswith(("https://", "http://")) for url in payload.sources):
        raise HTTPException(status_code=422, detail="Sources must be http(s) URLs")
    digest = hashlib.sha256(payload.content.strip().encode("utf-8")).hexdigest()
    try:
        with db() as conn:
            row = conn.execute(
                """INSERT INTO knowledge(content, kind, source_label, content_hash, status)
                   VALUES (%s, %s, %s, %s, 'pending_review')
                   ON CONFLICT (content_hash) DO NOTHING
                   RETURNING id, status, created_at""",
                (payload.content.strip(), payload.kind, payload.source_label, digest),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=409, detail="Duplicate knowledge item")
            item_id, status, created_at = row
            for url in payload.sources:
                conn.execute(
                    "INSERT INTO knowledge_sources(knowledge_id, url) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (item_id, url),
                )
            conn.execute(
                """INSERT INTO audit_events(entity_type, entity_id, event_type, actor, details)
                   VALUES ('knowledge', %s, 'submitted', 'api', %s)""",
                (item_id, Jsonb({"kind": payload.kind, "source_count": len(payload.sources)})),
            )
        return {"id": str(item_id), "status": status, "created_at": created_at.isoformat()}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Could not save knowledge")


@app.get("/knowledge")
def list_knowledge(status: str = "pending_review", limit: int = 50,
                   authorization: str | None = Header(default=None)):
    expected = os.environ.get("PROTON_API_KEY")
    if not expected or authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if status not in {"pending_review", "quarantined", "approved", "rejected", "declaration_unverified", "all"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    limit = max(1, min(limit, 100))
    with db() as conn:
        if status == "all":
            rows = conn.execute(
                "SELECT id, kind, status, guardian_verdict, training_eligible, created_at FROM knowledge ORDER BY created_at DESC LIMIT %s",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, kind, status, guardian_verdict, training_eligible, created_at FROM knowledge WHERE status=%s ORDER BY created_at DESC LIMIT %s",
                (status, limit),
            ).fetchall()
    return [{"id": str(r[0]), "kind": r[1], "status": r[2], "guardian_verdict": r[3],
             "training_eligible": r[4], "created_at": r[5].isoformat()} for r in rows]


@app.get("/knowledge/{item_id}")
def get_knowledge(item_id: UUID, authorization: str | None = Header(default=None)):
    expected = os.environ.get("PROTON_API_KEY")
    if not expected or authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    with db() as conn:
        row = conn.execute(
            "SELECT id, content, kind, source_label, status, guardian_verdict, training_eligible, created_at FROM knowledge WHERE id=%s",
            (item_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Not found")
        sources = conn.execute(
            "SELECT url, title FROM knowledge_sources WHERE knowledge_id=%s ORDER BY created_at",
            (item_id,),
        ).fetchall()
    return {"id": str(row[0]), "content": row[1], "kind": row[2], "source_label": row[3],
            "status": row[4], "guardian_verdict": row[5], "training_eligible": row[6],
            "created_at": row[7].isoformat(), "sources": [{"url": s[0], "title": s[1]} for s in sources]}


@app.get("/", include_in_schema=False)
def proton_home():
    """Serve the standalone Proton-AI chat interface."""
    page = Path(__file__).resolve().parent.parent / "ui" / "index.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="Proton-AI interface not installed")
    return FileResponse(page)

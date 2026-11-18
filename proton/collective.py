"""Collective knowledge exchange for Proton-AI.

Incoming contributions are proposals, never facts. Only reviewed lessons can be
exported to the neural-training corpus. Ownership claims remain unverified
declarations and are never presented as legal proof.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = "brawlstarsarthurgg415-byte/Proton-AI"
RAW_APPROVED_URL = f"https://raw.githubusercontent.com/{REPO}/main/collective/approved.jsonl"
ROOT = Path(__file__).resolve().parent.parent
OUTBOX = ROOT / "collective-outbox"
APPROVED = ROOT / "collective" / "approved.jsonl"
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
TOKEN_RE = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{8,}\d)(?!\w)")


class CollectiveError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(text: str) -> str:
    return " ".join(text.casefold().split())


def _contains_private_data(text: str) -> bool:
    return bool(EMAIL_RE.search(text) or TOKEN_RE.search(text) or PHONE_RE.search(text))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("schema") == "proton-lesson-v1":
            rows.append(item)
    return rows


def local_review(record: dict[str, Any], known: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Basic deterministic checks. These are NOT AI reviewers or fact-checkers."""
    content = str(record.get("content", "")).strip()
    reports = []
    reports.append({
        "reviewer": "local-privacy-check",
        "passed": not _contains_private_data(content),
        "message": "No obvious email, phone number or API-token pattern found."
        if not _contains_private_data(content) else "Possible personal data or secret detected; remove it.",
    })
    sources = record.get("sources", [])
    reports.append({
        "reviewer": "local-source-check",
        "passed": bool(sources) and all(
            isinstance(url, str) and url.startswith(("https://", "http://")) for url in sources
        ),
        "message": "At least one URL source was supplied."
        if sources and all(isinstance(url, str) and url.startswith(("https://", "http://")) for url in sources)
        else "Add at least one http(s) source. A URL alone does not prove the claim.",
    })
    duplicate = any(
        _canonical(str(item.get("content", ""))) == _canonical(content)
        for item in known
    )
    reports.append({
        "reviewer": "local-duplicate-check",
        "passed": not duplicate,
        "message": "No exact normalized duplicate found." if not duplicate else "An identical entry already exists.",
    })
    return reports


def submit(content: str, *, kind: str = "lesson", sources: list[str] | None = None,
           subject: str | None = None) -> dict[str, Any]:
    """Create a local proposal. Nothing is published automatically."""
    content = content.strip()
    if kind not in {"lesson", "ownership_claim", "correction"}:
        raise CollectiveError("kind must be lesson, ownership_claim or correction")
    if len(content) < 30 or len(content) > 6000:
        raise CollectiveError("content must contain between 30 and 6000 characters")
    if _contains_private_data(content):
        raise CollectiveError("Possible personal data or secret detected; remove it before submitting.")
    sources = sources or []
    if any(not isinstance(url, str) or not url.startswith(("https://", "http://")) for url in sources):
        raise CollectiveError("Every source must be an http(s) URL")
    if kind in {"lesson", "correction"} and not sources:
        raise CollectiveError("Lessons and corrections need at least one source URL")
    record = {
        "schema": "proton-lesson-v1",
        "id": str(uuid.uuid4()),
        "kind": kind,
        "subject": (subject or "").strip()[:160],
        "content": content,
        "sources": sources[:10],
        "created_at": _now(),
        "status": "pending_review",
        "review_reports": [],
        "external_reviews": [],
        "training_eligible": False,
    }
    known = _read_jsonl(APPROVED)
    reports = local_review(record, known)
    record["review_reports"] = reports
    record["local_checks_passed"] = all(item["passed"] for item in reports)
    if kind == "ownership_claim":
        record["status"] = "declaration_unverified"
        record["training_eligible"] = False
        record["notice"] = "User declaration only; not proof of legal ownership."
    OUTBOX.mkdir(parents=True, exist_ok=True)
    (OUTBOX / f"{record['id']}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


def receive(*, url: str = RAW_APPROVED_URL, timeout: int = 15) -> list[dict[str, Any]]:
    """Download the public approved feed; untrusted records are filtered."""
    request = urllib.request.Request(url, headers={"User-Agent": "Proton-AI-Collective/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(5_000_001)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CollectiveError(f"Could not download collective feed: {exc}") from exc
    if len(raw) > 5_000_000:
        raise CollectiveError("Collective feed is larger than the 5 MB safety limit.")
    rows = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (isinstance(item, dict) and item.get("schema") == "proton-lesson-v1"
                and item.get("kind") in {"lesson", "correction"}
                and item.get("status") == "approved"
                and item.get("training_eligible") is True
                and isinstance(item.get("content"), str)
                and not _contains_private_data(item["content"])):
            rows.append(item)
    return rows


def sync(*, url: str = RAW_APPROVED_URL) -> int:
    """Merge the approved feed into the local read-only cache."""
    incoming = receive(url=url)
    APPROVED.parent.mkdir(parents=True, exist_ok=True)
    existing = {item.get("id"): item for item in _read_jsonl(APPROVED)}
    for item in incoming:
        existing[item["id"]] = item
    temp = APPROVED.with_suffix(".tmp")
    temp.write_text(
        "".join(json.dumps(existing[key], ensure_ascii=False) + "\n" for key in sorted(existing)),
        encoding="utf-8",
    )
    temp.replace(APPROVED)
    return len(incoming)


def publish_pending(record_id: str, *, token: str | None = None) -> str:
    """Upload one proposal to a unique incoming path using a user's GitHub token.

    The token is read from PROTON_GITHUB_TOKEN and is never stored in Proton files.
    The repository must grant Contents: write. Publishing only opens a proposal;
    it does not approve the record or add it to neural training.
    """
    token = token or os.environ.get("PROTON_GITHUB_TOKEN")
    if not token:
        raise CollectiveError("Set PROTON_GITHUB_TOKEN with a GitHub token that has Contents: write.")
    path = OUTBOX / f"{record_id}.json"
    if not path.is_file():
        raise CollectiveError("Pending proposal not found.")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema") != "proton-lesson-v1" or record.get("status") not in {
        "pending_review", "declaration_unverified"
    }:
        raise CollectiveError("This proposal is not eligible for publication.")
    api_url = f"https://api.github.com/repos/{REPO}/contents/collective/incoming/{record_id}.json"
    body = json.dumps({
        "message": f"Propose collective contribution {record_id}",
        "content": __import__("base64").b64encode(
            json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("ascii"),
    }).encode("utf-8")
    request = urllib.request.Request(api_url, data=body, method="PUT", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Proton-AI-Collective/1.0",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise CollectiveError(f"GitHub rejected the proposal ({exc.code}): {detail}") from exc
    return result.get("content", {}).get("html_url", api_url)



def publish_all_pending(*, token: str | None = None) -> tuple[int, int]:
    """Retry queued uploads; failed/offline proposals remain in the outbox."""
    token = token or os.environ.get("PROTON_GITHUB_TOKEN")
    if not token:
        raise CollectiveError("Set PROTON_GITHUB_TOKEN to enable automatic uploads.")
    sent = failed = 0
    OUTBOX.mkdir(parents=True, exist_ok=True)
    for path in sorted(OUTBOX.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("published_at") or record.get("status") not in {
                "pending_review", "declaration_unverified"
            }:
                continue
            publish_pending(str(record["id"]), token=token)
            record["published_at"] = _now()
            record["publication_status"] = "uploaded_for_review"
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            sent += 1
        except (CollectiveError, OSError, KeyError, json.JSONDecodeError):
            failed += 1
    return sent, failed


def export_training_text(output: Path, *, approved_path: Path = APPROVED) -> int:
    """Export approved, source-backed lesson text for next-character training."""
    rows = _read_jsonl(approved_path)
    lessons = [
        item for item in rows
        if item.get("status") == "approved"
        and item.get("training_eligible") is True
        and item.get("kind") in {"lesson", "correction"}
        and item.get("sources")
        and not _contains_private_data(str(item.get("content", "")))
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n\n".join(str(item["content"]).strip() for item in lessons) + ("\n" if lessons else ""),
        encoding="utf-8",
    )
    return len(lessons)


def record_external_review(record_id: str, reviewer_id: str, decision: str,
                           rationale: str, *, outbox: Path = OUTBOX) -> dict[str, Any]:
    """Attach an independently supplied review. Caller must authenticate reviewer identity."""
    if decision not in {"approve", "reject", "needs_changes"}:
        raise CollectiveError("decision must be approve, reject or needs_changes")
    if not reviewer_id.strip() or len(rationale.strip()) < 20:
        raise CollectiveError("Reviewer ID and a rationale of at least 20 characters are required.")
    path = outbox / f"{record_id}.json"
    if not path.is_file():
        raise CollectiveError("Proposal not found.")
    record = json.loads(path.read_text(encoding="utf-8"))
    votes = record.setdefault("external_reviews", [])
    if any(vote.get("reviewer_id") == reviewer_id for vote in votes):
        raise CollectiveError("This reviewer has already reviewed this proposal.")
    votes.append({
        "reviewer_id": reviewer_id,
        "decision": decision,
        "rationale": rationale.strip()[:2000],
        "reviewed_at": _now(),
    })
    # Two distinct approving reviewers are necessary, but do not by themselves
    # establish truth; the maintainer's curation step is still required.
    approvals = {v["reviewer_id"] for v in votes if v["decision"] == "approve"}
    record["external_approval_count"] = len(approvals)
    record["status"] = "pending_curator" if len(approvals) >= 2 else "pending_review"
    record["training_eligible"] = False
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record

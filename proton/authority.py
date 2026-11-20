"""Proton Authority authentication and per-user administration API."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from uuid import UUID
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import psycopg
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

router = APIRouter(prefix="/authority", tags=["Proton Authority"])
DATABASE_URL = os.environ.get("DATABASE_URL")
ROLES = {"user", "official_admin", "ceo"}
SETTING_KEYS = {"personality", "conversation_style", "response_preferences"}


def db():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Authority database is not configured")
    return psycopg.connect(DATABASE_URL, connect_timeout=10)


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise HTTPException(status_code=503, detail=f"{name} is not configured")
    return value


def _check_global_password(candidate: str) -> None:
    if not hmac.compare_digest(candidate.encode(), _env("PROTON_PANEL_ACCESS_CODE").encode()):
        raise HTTPException(status_code=401, detail="Invalid global panel password")


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def _verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt_text, digest_text = encoded.split("$", 2)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _fernet() -> Fernet:
    try:
        return Fernet(_env("PROTON_TOTP_ENCRYPTION_KEY").encode())
    except Exception:
        raise HTTPException(status_code=503, detail="Invalid TOTP encryption key")


def _new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _totp(secret: str, at: int | None = None) -> str:
    key = base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8))
    counter = int((at if at is not None else time.time()) // 30)
    digest = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 15
    value = (int.from_bytes(digest[offset:offset + 4], "big") & 0x7fffffff) % 1_000_000
    return f"{value:06d}"


def _verify_totp(secret: str, code: str) -> bool:
    if len(code) != 6 or not code.isdigit():
        return False
    now = int(time.time())
    return any(hmac.compare_digest(_totp(secret, now + delta * 30), code) for delta in (-1, 0, 1))


def _audit(conn, actor: str, event: str, details: dict, entity_id=None):
    conn.execute(
        """INSERT INTO audit_events(entity_type, entity_id, event_type, actor, details)
           VALUES ('authority', %s, %s, %s, %s)""",
        (entity_id, event, actor, Jsonb(details)),
    )


class RegisterInput(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=128)
    global_password: str = Field(min_length=1, max_length=256)
    owner_bootstrap_code: str | None = Field(default=None, max_length=256)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=12, max_length=128)
    global_password: str = Field(min_length=1, max_length=256)


class TwoFactorConfirm(Credentials):
    code: str = Field(pattern=r"^[0-9]{6}$")


class RoleChange(BaseModel):
    role: str = Field(pattern=r"^(user|official_admin)$")


class SettingsChange(BaseModel):
    settings: dict = Field(default_factory=dict)


def _get_account(username: str):
    with db() as conn:
        return conn.execute(
            """SELECT id, username, password_hash, role, totp_secret, totp_enabled
               FROM authority_users WHERE username=%s""",
            (username.lower(),),
        ).fetchone()


def _check_credentials(payload: Credentials):
    _check_global_password(payload.global_password)
    row = _get_account(payload.username)
    if row is None or not _verify_password(payload.password, row[2]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return row


def _current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer session required")
    token_hash = hashlib.sha256(authorization[7:].strip().encode()).hexdigest()
    with db() as conn:
        row = conn.execute(
            """SELECT u.id, u.username, u.role
               FROM authority_sessions s JOIN authority_users u ON u.id=s.user_id
               WHERE s.token_hash=%s AND s.revoked_at IS NULL AND s.expires_at > NOW()""",
            (token_hash,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Session expired or revoked")
    return row


def _require_official(user):
    if user[2] not in {"ceo", "official_admin"}:
        raise HTTPException(status_code=403, detail="Official administrator permission required")


def _require_ceo(user):
    if user[2] != "ceo":
        raise HTTPException(status_code=403, detail="CEO permission required")


@router.post("/register", status_code=201)
def register(payload: RegisterInput):
    _check_global_password(payload.global_password)
    username = payload.username.lower()
    owner_username = _env("PROTON_OWNER_USERNAME").lower()
    role = "user"
    if username == owner_username:
        bootstrap = _env("PROTON_OWNER_BOOTSTRAP_CODE")
        if not payload.owner_bootstrap_code or not hmac.compare_digest(
            payload.owner_bootstrap_code.encode(), bootstrap.encode()
        ):
            raise HTTPException(status_code=403, detail="Owner bootstrap authorization required")
        role = "ceo"
    try:
        with db() as conn:
            row = conn.execute(
                """INSERT INTO authority_users(username, password_hash, role)
                   VALUES (%s, %s, %s) RETURNING id, username, role""",
                (username, _password_hash(payload.password), role),
            ).fetchone()
            _audit(conn, username, "account_registered", {"role": role}, row[0])
        return {"id": str(row[0]), "username": row[1], "role": row[2], "next_step": "setup_authenticator"}
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Username already exists")


@router.post("/2fa/setup")
def setup_2fa(payload: Credentials):
    row = _check_credentials(payload)
    if row[5]:
        raise HTTPException(status_code=409, detail="Authenticator is already enabled")
    secret = _new_totp_secret()
    encrypted = _fernet().encrypt(secret.encode()).decode()
    with db() as conn:
        conn.execute("UPDATE authority_users SET totp_secret=%s, totp_enabled=FALSE WHERE id=%s", (encrypted, row[0]))
        _audit(conn, row[1], "totp_setup_started", {}, row[0])
    issuer = "Proton-AI"
    uri = f"otpauth://totp/{quote(issuer)}:{quote(row[1])}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"
    return {"secret": secret, "otpauth_uri": uri, "warning": "Save this secret only in your authenticator. Never share it."}


@router.post("/2fa/confirm")
def confirm_2fa(payload: TwoFactorConfirm):
    row = _check_credentials(payload)
    if not row[4]:
        raise HTTPException(status_code=409, detail="Start authenticator setup first")
    try:
        secret = _fernet().decrypt(row[4].encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=503, detail="Could not decrypt authenticator secret")
    if not _verify_totp(secret, payload.code):
        raise HTTPException(status_code=401, detail="Invalid authenticator code")
    with db() as conn:
        conn.execute("UPDATE authority_users SET totp_enabled=TRUE WHERE id=%s", (row[0],))
        _audit(conn, row[1], "totp_enabled", {}, row[0])
    return {"status": "enabled"}


@router.post("/login")
def login(payload: TwoFactorConfirm):
    row = _check_credentials(payload)
    if not row[5] or not row[4]:
        raise HTTPException(status_code=403, detail="Authenticator enrollment is required")
    try:
        secret = _fernet().decrypt(row[4].encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=503, detail="Could not decrypt authenticator secret")
    if not _verify_totp(secret, payload.code):
        raise HTTPException(status_code=401, detail="Invalid authenticator code")
    token = secrets.token_urlsafe(40)
    expires = datetime.now(timezone.utc) + timedelta(hours=12)
    with db() as conn:
        conn.execute(
            "INSERT INTO authority_sessions(user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (row[0], hashlib.sha256(token.encode()).hexdigest(), expires),
        )
        _audit(conn, row[1], "login_succeeded", {"expires_at": expires.isoformat()}, row[0])
    return {"access_token": token, "token_type": "bearer", "expires_at": expires.isoformat(), "role": row[3]}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    token_hash = hashlib.sha256(authorization[7:].strip().encode()).hexdigest()
    with db() as conn:
        conn.execute("UPDATE authority_sessions SET revoked_at=NOW() WHERE token_hash=%s", (token_hash,))
        _audit(conn, user[1], "logout", {}, user[0])
    return {"status": "logged_out"}


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    return {"id": str(user[0]), "username": user[1], "role": user[2]}


@router.get("/me/settings")
def get_my_settings(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    with db() as conn:
        row = conn.execute("SELECT settings FROM authority_ai_profiles WHERE user_id=%s", (user[0],)).fetchone()
    return {"settings": row[0] if row else {}}


@router.patch("/me/settings")
def update_my_settings(payload: SettingsChange, authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    if not set(payload.settings).issubset(SETTING_KEYS):
        raise HTTPException(status_code=400, detail="Only basic personal AI settings can be changed")
    if any(not isinstance(v, str) or len(v) > 500 for v in payload.settings.values()):
        raise HTTPException(status_code=422, detail="Setting values must be text up to 500 characters")
    with db() as conn:
        conn.execute(
            """INSERT INTO authority_ai_profiles(user_id, settings) VALUES (%s, %s)
               ON CONFLICT (user_id) DO UPDATE SET settings=authority_ai_profiles.settings || EXCLUDED.settings,
               updated_at=NOW()""",
            (user[0], Jsonb(payload.settings)),
        )
        _audit(conn, user[1], "personal_ai_settings_updated", {"keys": sorted(payload.settings)}, user[0])
    return {"status": "saved", "settings": payload.settings}


@router.delete("/me/memory")
def clear_my_memory(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    with db() as conn:
        deleted = conn.execute("DELETE FROM authority_ai_memories WHERE user_id=%s", (user[0],)).rowcount
        _audit(conn, user[1], "own_ai_memory_cleared", {"deleted_items": deleted}, user[0])
    return {"status": "cleared", "deleted_items": deleted}


@router.get("/admin/users")
def list_users(authorization: str | None = Header(default=None)):
    actor = _current_user(authorization)
    _require_official(actor)
    with db() as conn:
        rows = conn.execute("SELECT id, username, role, created_at FROM authority_users ORDER BY created_at").fetchall()
    return [{"id": str(r[0]), "username": r[1], "role": r[2], "created_at": r[3].isoformat()} for r in rows]


@router.patch("/admin/users/{user_id}/role")
def change_role(user_id: UUID, payload: RoleChange, authorization: str | None = Header(default=None)):
    actor = _current_user(authorization)
    _require_ceo(actor)
    with db() as conn:
        target = conn.execute("SELECT id, username, role FROM authority_users WHERE id=%s", (user_id,)).fetchone()
        if target is None:
            raise HTTPException(status_code=404, detail="User not found")
        if target[2] == "ceo":
            raise HTTPException(status_code=403, detail="CEO role cannot be changed through this endpoint")
        conn.execute("UPDATE authority_users SET role=%s WHERE id=%s", (payload.role, target[0]))
        _audit(conn, actor[1], "user_role_changed", {"target": target[1], "new_role": payload.role}, target[0])
    return {"user": target[1], "role": payload.role}


@router.get("/admin/audit")
def audit_log(limit: int = 50, authorization: str | None = Header(default=None)):
    actor = _current_user(authorization)
    _require_official(actor)
    limit = max(1, min(limit, 100))
    with db() as conn:
        rows = conn.execute(
            """SELECT event_type, actor, details, created_at FROM audit_events
               WHERE entity_type='authority' ORDER BY created_at DESC LIMIT %s""",
            (limit,),
        ).fetchall()
    return [{"event": r[0], "actor": r[1], "details": r[2], "created_at": r[3].isoformat()} for r in rows]

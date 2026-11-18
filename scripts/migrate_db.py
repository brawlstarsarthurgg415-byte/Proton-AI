"""Apply Proton-AI SQL migrations safely and idempotently."""
from __future__ import annotations

import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is required")
    files = sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql"))
    if not files:
        raise SystemExit("No SQL migrations found")
    with psycopg.connect(url, autocommit=False, connect_timeout=15) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proton_schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        for path in files:
            exists = conn.execute(
                "SELECT 1 FROM proton_schema_migrations WHERE filename = %s",
                (path.name,),
            ).fetchone()
            if exists:
                print(f"already applied: {path.name}")
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO proton_schema_migrations(filename) VALUES (%s)",
                (path.name,),
            )
            print(f"applied: {path.name}")
    print("Proton-AI database migrations complete")


if __name__ == "__main__":
    main()

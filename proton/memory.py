"""Small, local JSON memory for the first Proton prototype."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path("data/knowledge.json")


class Memory:
    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else []

    def _write(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def add(self, text: str, source: str = "user") -> dict[str, Any]:
        clean = " ".join(text.split())
        if not clean:
            raise ValueError("O conhecimento não pode estar vazio.")
        items = self._read()
        item = {
            "id": len(items) + 1,
            "text": clean,
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        items.append(item)
        self._write(items)
        return item

    def all(self) -> list[dict[str, Any]]:
        return self._read()

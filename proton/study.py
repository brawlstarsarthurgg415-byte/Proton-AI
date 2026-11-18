"""Resumable, low-CPU curriculum study sessions; this does not train neural weights."""
from __future__ import annotations

import argparse
import json
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .curriculum import CURRICULUM

DEFAULT_PROGRESS = Path("data/study_progress.json")
_stop_requested = False


def _request_stop(signum: int, frame: Any) -> None:
    global _stop_requested
    _stop_requested = True


class StudySession:
    def __init__(self, progress_path: str | Path = DEFAULT_PROGRESS) -> None:
        self.progress_path = Path(progress_path)
        self.progress_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> dict:
        try:
            state = json.loads(self.progress_path.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                return state
        except (OSError, json.JSONDecodeError):
            pass
        return {"completed": [], "reviews": 0, "sessions": 0, "last_lesson": None}

    def checkpoint(self) -> None:
        self.progress_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.progress_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.progress_path)

    def run(self, hours: float = 15, interval_seconds: float = 60, max_cycles: int | None = None) -> dict:
        if hours <= 0 or interval_seconds < 0:
            raise ValueError("Informe horas positivas e intervalo não negativo.")
        deadline = time.monotonic() + hours * 3600
        self.state["sessions"] = int(self.state.get("sessions", 0)) + 1
        self.state["started_at"] = datetime.now(timezone.utc).isoformat()
        self.state["target_hours"] = hours
        self.checkpoint()
        cycle = 0
        index = int(self.state.get("next_index", 0)) % len(CURRICULUM)
        while time.monotonic() < deadline and not _stop_requested:
            lesson = CURRICULUM[index]
            key = f'{lesson["subject"]}:{lesson["title"]}'
            completed = self.state.setdefault("completed", [])
            if key not in completed:
                completed.append(key)
            self.state["last_lesson"] = key
            self.state["last_studied_at"] = datetime.now(timezone.utc).isoformat()
            self.state["reviews"] = int(self.state.get("reviews", 0)) + 1
            index = (index + 1) % len(CURRICULUM)
            self.state["next_index"] = index
            cycle += 1
            self.checkpoint()
            print(f'Estudado: {lesson["subject"]} — {lesson["title"]} | progresso: {len(completed)}/{len(CURRICULUM)} lições')
            if max_cycles is not None and cycle >= max_cycles:
                break
            remaining = deadline - time.monotonic()
            if remaining > 0 and interval_seconds:
                time.sleep(min(interval_seconds, remaining))
        self.state["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.state["last_session_status"] = "interrompida" if _stop_requested else "concluída"
        self.checkpoint()
        return self.state


def main() -> None:
    parser = argparse.ArgumentParser(description="Sessão de estudos contínuos do Proton")
    parser.add_argument("--hours", type=float, default=15, help="duração da sessão (padrão: 15 horas)")
    parser.add_argument("--interval", type=float, default=60, help="pausa entre lições em segundos (padrão: 60)")
    parser.add_argument("--progress", default=str(DEFAULT_PROGRESS), help="arquivo de checkpoint")
    args = parser.parse_args()
    signal.signal(signal.SIGINT, _request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _request_stop)
    print(f"Proton Study iniciado: {args.hours:g} horas. Use Ctrl+C para parar; o progresso será salvo.")
    print("Modo curricular offline: organiza revisões, mas não treina pesos de uma rede neural.")
    state = StudySession(args.progress).run(args.hours, args.interval)
    print(f'Sessão {state["last_session_status"]}. Checkpoint: {args.progress}')


if __name__ == "__main__":
    main()

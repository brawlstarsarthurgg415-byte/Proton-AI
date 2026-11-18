"""Small deterministic review agents; they do not verify factual truth."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import os
import re
from typing import Callable

from ..memory import Memory


@dataclass(frozen=True)
class TeacherReport:
    name: str
    passed: bool
    message: str


class LocalTeacher:
    """Runs independent local checks in parallel before a lesson is saved."""

    def __init__(self, memory: Memory, max_workers: int | None = None) -> None:
        self.memory = memory
        cpu_count = os.cpu_count() or 1
        self.max_workers = max(1, min(max_workers or 3, cpu_count, 3))
        self._checks: tuple[tuple[str, Callable[[str, str], TeacherReport]], ...] = (
            ("clareza", self._check_clarity),
            ("origem", self._check_source),
            ("duplicidade", self._check_duplicate),
        )

    @staticmethod
    def _check_clarity(text: str, source: str) -> TeacherReport:
        words = re.findall(r"[\wÀ-ÿ]+", text)
        passed = len(words) >= 2
        message = "Anotação tem conteúdo suficiente para ser armazenada." if passed else "Adicione uma frase mais completa (pelo menos duas palavras)."
        return TeacherReport("clareza", passed, message)

    @staticmethod
    def _check_source(text: str, source: str) -> TeacherReport:
        known_source = bool(source.strip())
        message = (
            f"Origem registrada: {source.strip()}. Isso identifica quem forneceu o texto, mas não comprova que ele seja verdadeiro."
            if known_source else "Informe a origem da anotação."
        )
        return TeacherReport("origem", known_source, message)

    def _check_duplicate(self, text: str, source: str) -> TeacherReport:
        normalized = " ".join(text.casefold().split())
        duplicate = any(" ".join(str(item.get("text", "")).casefold().split()) == normalized
                        for item in self.memory.all())
        return TeacherReport(
            "duplicidade", not duplicate,
            "Essa anotação já existe na memória." if duplicate else "Nenhuma cópia idêntica encontrada."
        )

    def review(self, text: str, source: str = "user") -> list[TeacherReport]:
        clean = " ".join(text.split())
        if not clean:
            return [TeacherReport("entrada", False, "O texto está vazio.")]
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = [pool.submit(check, clean, source) for _, check in self._checks]
            return [future.result() for future in futures]

    def submit(self, text: str, source: str = "user") -> tuple[dict | None, list[TeacherReport]]:
        reports = self.review(text, source)
        if not all(report.passed for report in reports):
            return None, reports
        item = self.memory.add(text, source=source)
        item["review"] = "passed_local_checks"
        return item, reports

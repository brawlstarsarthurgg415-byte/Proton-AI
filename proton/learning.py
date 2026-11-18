"""Lesson intake pipeline: review structure, then store locally."""
from __future__ import annotations

from .memory import Memory
from .teachers.local import LocalTeacher, TeacherReport


class LearningPipeline:
    def __init__(self, memory: Memory | None = None, teachers: LocalTeacher | None = None) -> None:
        self.memory = memory or Memory()
        self.teachers = teachers or LocalTeacher(self.memory)

    def submit(self, text: str, source: str = "user") -> tuple[dict | None, list[TeacherReport]]:
        return self.teachers.submit(text, source)

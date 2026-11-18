"""Teacher helpers for reviewing lessons and starter examples.

These are deterministic validation helpers, not independent neural AI models.
"""
from __future__ import annotations

from dataclasses import dataclass

from .local import LocalTeacher, TeacherReport


@dataclass
class Review:
    teacher: str
    passed: bool
    feedback: str


class TeacherAgent:
    name = "general"

    def review(self, text: str) -> Review:
        clean = text.strip()
        if len(clean) < 12:
            return Review(self.name, False, "Add a fuller explanation or example.")
        if len(clean) > 5000:
            return Review(self.name, False, "Split this into smaller learning examples.")
        return Review(self.name, True, "Example passed the basic length check.")


class ProgrammingTeacher(TeacherAgent):
    name = "programming"

    def review(self, text: str) -> Review:
        base = super().review(text)
        if not base.passed:
            return base
        terms = ("code", "function", "variable", "program", "algorithm")
        if not any(term in text.casefold() for term in terms):
            return Review(self.name, False, "Add a programming concept or label this for another subject.")
        return Review(self.name, True, "Programming example passed the basic subject check.")


class ScienceTeacher(TeacherAgent):
    name = "science"

    def review(self, text: str) -> Review:
        base = super().review(text)
        if not base.passed:
            return base
        terms = ("science", "energy", "atom", "planet", "cell", "force")
        if not any(term in text.casefold() for term in terms):
            return Review(self.name, False, "Add a science concept or label this for another subject.")
        return Review(self.name, True, "Science example passed the basic subject check.")


def available_teachers() -> list[TeacherAgent]:
    """Return deterministic example reviewers; these are not LLM teachers."""
    return [TeacherAgent(), ProgrammingTeacher(), ScienceTeacher()]


__all__ = [
    "LocalTeacher",
    "TeacherReport",
    "Review",
    "TeacherAgent",
    "ProgrammingTeacher",
    "ScienceTeacher",
    "available_teachers",
]

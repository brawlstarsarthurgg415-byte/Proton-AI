"""Separate teacher helpers; these are validators, not neural language models."""
from __future__ import annotations

from dataclasses import dataclass


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
        return Review(self.name, True, "Example is suitable for the starter dataset.")


class ProgrammingTeacher(TeacherAgent):
    name = "programming"

    def review(self, text: str) -> Review:
        base = super().review(text)
        if not base.passed:
            return base
        if not any(term in text.lower() for term in ("code", "function", "variable", "program", "algorithm")):
            return Review(self.name, False, "Add a programming concept or label this for another subject.")
        return Review(self.name, True, "Programming example passed the basic subject check.")


class ScienceTeacher(TeacherAgent):
    name = "science"

    def review(self, text: str) -> Review:
        base = super().review(text)
        if not base.passed:
            return base
        if not any(term in text.lower() for term in ("science", "energy", "atom", "planet", "cell", "force")):
            return Review(self.name, False, "Add a science concept or label this for another subject.")
        return Review(self.name, True, "Science example passed the basic subject check.")


def available_teachers() -> list[TeacherAgent]:
    return [TeacherAgent(), ProgrammingTeacher(), ScienceTeacher()]

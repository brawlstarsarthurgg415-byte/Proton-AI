"""Transparent baseline retrieval and session chat for Proton."""
from __future__ import annotations

import re
from collections import Counter

from .memory import Memory
from .personality import BrazilianPersonality


def terms(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ]+", text.casefold())


class Proton:
    def __init__(self, memory: Memory | None = None) -> None:
        self.memory = memory or Memory()
        self.personality = BrazilianPersonality()

    def learn(self, text: str, source: str = "user") -> dict:
        return self.memory.add(text, source=source)

    def chat(self, message: str) -> str:
        """Reply in the informal Brazilian style, keeping session-level banter."""
        return self.personality.reply(message)

    def ask(self, question: str) -> list[dict]:
        query = Counter(terms(question))
        if not query:
            return []
        ranked = []
        for item in self.memory.all():
            words = Counter(terms(item.get("text", "")))
            score = sum(min(count, words[word]) for word, count in query.items())
            if score:
                ranked.append((score, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in ranked[:5]]

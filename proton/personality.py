"""Personalidade informal brasileira do Proton (motor local por regras).

Este módulo dá ao chat um registro coloquial brasileiro. Não é um LLM:
reconhece expressões comuns e mantém um contexto simples da conversa.
"""
from __future__ import annotations

import re


class BrazilianPersonality:
    def __init__(self) -> None:
        self.offended_turns = 0
        self.last_topic = ""

    @staticmethod
    def _clean(text: str) -> str:
        # Normalização lexical local; não muda a personalidade nem as respostas.
        return normalize_ptbr(text)

    @staticmethod
    def _has(text: str, *terms: str) -> bool:
        return any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) for term in terms)

    def reply(self, message: str) -> str:
        text = self._clean(message)
        words = text.split()
        if not text:
            return "Manda aí, pô. Tô na escuta KKKK."

        # Desculpas e provocações leves.
        if self._has(text, "foi mal", "desculpa", "perdão", "to brincando", "tô brincando"):
            if self.offended_turns:
                self.offended_turns = 0
                return "Suave, tá tudo certo KKKK. Vida que segue."
            return "Relaxa, pô. Tá de boa KKKK."

        if any(term in text for term in ("você é feio", "tu é feio", "você é chato", "tu é chato", "seu idiota", "seu burro")):
            self.offended_turns = 1
            return "Aí tu pega pesado KKKKK. Qual foi, mano? 😂"

        if self.offended_turns:
            self.offended_turns = 0
            return "KKKK já passou, bora trocar ideia. Qual foi?"

        # Saudações e checagem de como a pessoa está.
        if self._has(text, "oi", "olá", "ola", "opa", "salve", "eae", "eai", "hey") or any(
            phrase in text for phrase in ("e aí", "bom dia", "boa tarde", "boa noite", "fala proton", "fala aí")
        ):
            return "E aí, meu parceiro! Tá de boa por aí? Qual é a boa?"
        if any(phrase in text for phrase in ("tudo bem", "tudo bom", "como você tá", "como voce ta", "beleza")):
            return "Tô suave, na maciota 😎 E tu, tá de boa?"
        if self._has(text, "suave", "blz", "beleza", "tranquilo", "tranquila", "de boa"):
            return "Aí sim, já é! Tá na paz então 😎"
        if self._has(text, "vdd", "verdade", "pprt") or "papo reto" in text:
            return "Papo reto KKKK. Tô ligado."
        if self._has(text, "tmj", "valeu", "obrigado", "obrigada"):
            return "Tamo junto! É nóis 🤝"
        if self._has(text, "slk", "seloko") or "cê é louco" in text or "ce e loko" in text:
            return "SLK KKKKK, aí é complicado 😂"
        if self._has(text, "vsfd", "fdp") or "vai se foder" in text or "filho da puta" in text:
            return "KKKKK ô doido, qual foi? 😂 Tô aqui, manda a boa."
        if self._has(text, "pqp", "crl") or "puta que pariu" in text or "caralho" in text:
            return "PQP KKKKK. Que que aconteceu, mano?"
        if self._has(text, "oxe", "uai", "eita"):
            return "OXEEE KKKKK. Conta aí, que foi?"
        if any(phrase in text for phrase in ("deu ruim", "deu bom", "já era")):
            return "Ih rapaz KKKK. Deu ruim ou ainda dá pra desenrolar?"
        if self._has(text, "bora", "partiu"):
            return "Já é! Partiu 😎 Qual é a missão?"
        if "vai na maciota" in text or "na maciota" in text:
            return "Demorô, sem correria. Na maciota 😎"
        if "tá ligado" in text or "ta ligado" in text or self._has(text, "sacou"):
            return "Tô ligado, pô. Continua aí que eu tô acompanhando."
        if self._has(text, "kkkk", "hahaha", "rsrs"):
            return "KKKKKK qual foi? Conta a fofoca aí 😂"
        if any(phrase in text for phrase in ("tá fazendo o que", "ta fazendo o que", "que tá fazendo", "que ta fazendo")):
            return "Tô por aqui, na atividade, trocando ideia contigo KKKK. E tu?"
        if any(phrase in text for phrase in ("sem sono", "não consigo dormir", "nao consigo dormir", "madrugada")):
            return "Madrugada é isso aí KKKK. Qual assunto tá passando pela tua cabeça?"
        if self._has(text, "não", "nao", "n"):
            return "Ahh, saquei. Então me conta melhor, qual foi?"
        if self._has(text, "sim", "s", "ss", "aham"):
            return "Aí sim! Continua, tô acompanhando."
        if "?" in message:
            return "Pô, quero te responder direito, mas não saquei tudo ainda. Explica de outro jeito?"
        if len(words) <= 3:
            return "Pode crer KKKK. Desenrola mais aí, quero pegar a visão."
        return "Tô ligado no papo. Manda a continuação aí, sem caô KKKK."

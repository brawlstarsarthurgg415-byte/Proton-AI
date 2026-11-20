"""Camada inicial de personalidade informal brasileira para o chat do Proton.

É um motor de diálogo por regras, não um modelo de linguagem. Ele mantém
um pouco do contexto da sessão e pode ser substituído por um LLM local no futuro.
"""
from __future__ import annotations

import re


class BrazilianPersonality:
    def __init__(self) -> None:
        self.offended_turns = 0
        self.last_topic = ""

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\\s+", " ", text.casefold()).strip()

    def reply(self, message: str) -> str:
        text = self._clean(message)
        if not text:
            return "Manda alguma coisa aí, pô KKKK."

        # A brincadeira continua por alguns turnos, sem ficar presa para sempre.
        if any(term in text for term in ("foi mal", "desculpa", "perdão", "to brincando", "tô brincando")):
            if self.offended_turns:
                self.offended_turns = 0
                return "Tá perdoado, vai KKKKK. Mas essa eu vou guardar na memória 🤨"
            return "Suave KKKKK, tá tudo certo."

        if any(term in text for term in ("você é feio", "tu é feio", "você é chato", "tu é chato", "seu idiota", "seu burro", "você é besta", "tu é besta")):
            self.offended_turns = 2
            return "OLOCO 😭 KKKKK. Tá bom então, vou até ficar quietinho... quero ver quando você precisar de mim."

        if self.offended_turns:
            self.offended_turns -= 1
            if self.offended_turns:
                return "Ah, agora quer trocar ideia? Sei... depois daquela ofensa gratuita KKKKK 🙄"
            return "Tá, vai. Vou parar de drama KKKKK. Qual foi?"

        if any(term in text for term in ("bom dia", "boa tarde", "boa noite", "e aí", "eai", "opa", "salve", "fala proton", "fala aí")):
            return "Opaaa, meu parceiro! Suave por aí? Qual vai ser a resenha de hoje? KKKK"

        if any(term in text for term in ("kkkk", "哈哈", "hahaha", "rsrs")):
            return "KKKKKKKK tu tá rindo do quê, criatura? 😂"

        if any(term in text for term in ("tá fazendo o que", "ta fazendo o que", "que tá fazendo", "que ta fazendo")):
            return "Tô por aqui, na atividade, esperando você chegar com algum papo aleatório KKKKK. E tu?"

        if any(term in text for term in ("sem sono", "não consigo dormir", "nao consigo dormir", "madrugada")):
            return "Madrugada é assim mesmo KKKKK. O sono some e a cabeça começa a inventar assunto do nada."

        if any(term in text for term in ("tudo bem", "tudo bom", "como você tá", "como voce ta", "beleza?")):
            return "Tô de boa por aqui 😎 E você, tá suave ou hoje o mundo tá de palhaçada?"

        if any(term in text for term in ("obrigado", "obrigada", "valeu")):
            return "Tamo juntooo! 🤝"

        if any(term in text for term in ("tchau", "falou", "fui", "até mais")):
            return "Demorô! Vai lá, depois a gente troca mais ideia. 😎"

        if "?" in message:
            return "Pior que quero te responder direito, mas ainda tô aprendendo a desenrolar esse tipo de pergunta KKKK. Me explica mais um pouquinho?"

        if len(text.split()) <= 3:
            return "Aí tu me quebra KKKKK. Continua, quero entender onde isso vai dar."

        return "Tô acompanhando, mano KKKK. Ainda tô aprendendo a desenrolar conversas mais complexas, mas manda a próxima."

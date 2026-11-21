"""Normalização lexical local para português brasileiro informal.

Expande abreviações e variantes comuns antes do motor de diálogo.
Não usa rede, serviços externos ou modelos. Mantém o texto original quando
não conhece uma expressão; não tenta adivinhar palavras desconhecidas.
"""
from __future__ import annotations

import re
import unicodedata

# Abreviações de chat e gírias frequentes. Os valores são formas legíveis,
# não respostas: a personalidade continua responsável pelo jeito de falar.
SLANG = {
    "vc": "você", "vcs": "vocês", "c": "você", "ce": "você",
    "tb": "também", "tbm": "também", "tmb": "também",
    "pq": "porque", "pqq": "porque", "q": "que", "oq": "o que",
    "kd": "cadê", "cade": "cadê", "nd": "nada", "n": "não",
    "naum": "não", "num": "não", "ss": "sim", "s": "sim",
    "blz": "beleza", "bllz": "beleza", "dboas": "de boas",
    "suave": "suave", "demoro": "demorou", "demorô": "demorou",
    "jae": "já é", "ja": "já", "eae": "e aí", "eai": "e aí",
    "iae": "e aí", "opa": "opa", "salve": "salve",
    "tmj": "tamo junto", "flw": "falou", "vlw": "valeu",
    " obg": " obrigado", "obg": "obrigado", " pf": " por favor",
    "pfv": "por favor", "pls": "por favor", "fds": "fim de semana",
    "vdd": "verdade", "pprt": "papo reto", "slk": "cê é louco",
    "slc": "cê é louco", "mlk": "moleque", "mn": "mano",
    "mano": "mano", "parça": "parceiro", "parca": "parceiro",
    "véi": "velho", "vei": "velho", "pdc": "pode crer",
    "ctz": "certeza", "certeza": "certeza", "ata": "ah tá",
    "aff": "aff", "mds": "meu deus", " jesus": " jesus",
    "pqp": "puta que pariu", "vsfd": "vai se foder",
    "vtnc": "vai tomar no cu", "fdp": "filho da puta",
    "crl": "caralho", "krl": "caralho", "carai": "caralho",
    "kk": "kkk", "kkkk": "kkkk", "rs": "rsrs",
    "rindo": "rindo", "nss": "nossa", "nossa": "nossa",
    "oxe": "oxe", "uai": "uai", "eita": "eita",
    "bora": "bora", "partiu": "partiu", "tlg": "tá ligado",
    "tlgd": "tá ligado", "sacou": "sacou", "né": "né",
    "nao": "não", "to": "tô", "ta": "tá", "tava": "estava",
    "pro": "para o", "pra": "para", "qnd": "quando",
    "quando": "quando", "hj": "hoje", "ont": "ontem",
    "amanha": "amanhã", "agr": "agora", "dps": "depois",
    "depois": "depois", "mt": "muito", "mto": "muito",
    "pouco": "pouco", " obg": " obrigado",
}

# Pequenas correções de digitação que não dependem de adivinhar contexto.
TYPOS = {
    "dboas": "de boas", "boas": "boas", "eaii": "e aí",
    "oii": "oi", "oiiii": "oi", "obgdo": "obrigado",
    "brigado": "obrigado", "brigada": "obrigada",
    "naum": "não", "concerteza": "com certeza",
}


def normalize_ptbr(text: str) -> str:
    """Expande abreviações conhecidas e preserva pontuação e termos desconhecidos."""
    value = text.casefold()
    value = re.sub(r"\s+", " ", value).strip()
    tokens = re.findall(r"[^\W_]+|[^\w\s]", value, flags=re.UNICODE)
    normalized: list[str] = []
    for token in tokens:
        replacement = TYPOS.get(token, SLANG.get(token, token))
        normalized.append(replacement)
    result = " ".join(normalized)
    # Recoloca pontuação sem espaços antes dela.
    result = re.sub(r"\s+([?!.,;:])", r"\1", result)
    return result

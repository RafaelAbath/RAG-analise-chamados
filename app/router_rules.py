import re
KEYWORD_SECTOR_RULES: list[tuple[str, str]] = [
    (r"\b(opme)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(opme)\b",
     "NIP Reclames e judiciais OPME"),
    (r"\b(home\s*care|hc)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(home\s*care|hc)\b",
     "NIP Reclames e judiciais HC"),
    (r"\bopme\b",                     "OPME"),
    (r"\b(ans|nip)\b",                "Judiciais + NIPs"),
]

def route_by_keywords(text: str) -> str | None:
    for pattern, setor in KEYWORD_SECTOR_RULES:
        if re.search(pattern, text, flags=re.I):
            return setor
    return None

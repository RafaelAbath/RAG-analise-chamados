import re

KEYWORD_SECTOR_RULES: list[tuple[str, str]] = [
    # 1) NIP/Judiciais + OPME
    (r"\b(opme)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(opme)\b",
     "NIP Reclames e judiciais OPME"),

    # 2) NIP/Judiciais + Home Care
    (r"\b(home\s*care|hc)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(home\s*care|hc)\b",
     "NIP Reclames e judiciais HC"),

    # 3) **Beneficiário / Coparticipação → Faturamento (Jorgete)**
    (r"\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|"
     r"demonstrativo[s]?|glosa[s]?|portal\s+sa[úu]de\s+caixa|"
     r"chave\s+eletr[oô]nica|xml)\b",
     "Faturamento"),

    # 4) **Nota fiscal / Impostos de prestador → Financeiro / Tributos**
    (r"\b(nota[s]?\s+fiscal(?:is)?|issqn|inss|cadastro\s+tribut[áa]rio|"
     r"reten[cç][aã]o|imposto[s]?|prestador(?:es)?)\b",
     "Financeiro / Tributos"),

    # 5) OPME puro
    (r"\bopme\b", "OPME"),

    # 6) ANS / NIP genérico
    (r"\b(ans|nip)\b", "Judiciais + NIPs"),
]

def route_by_keywords(text: str) -> str | None:
    for pattern, setor in KEYWORD_SECTOR_RULES:
        if re.search(pattern, text, flags=re.I):
            return setor
    return None

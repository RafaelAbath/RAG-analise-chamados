import re

KEYWORD_SECTOR_RULES: list[tuple[str, str]] = [
    (r"(?i)(?=.*\bcontato\b)(?=.*\bwhatsapp\b)",
     "Garantia de Atendimento (Busca de rede)"),
    
    (r"\b(opme)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(opme)\b",
     "NIP Reclames e judiciais OPME"),

    
    (r"\b(home\s*care|hc)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(home\s*care|hc)\b",
     "NIP Reclames e judiciais HC"),
    (r"\b(cpap|aparelho|lente|catarata|pr[oô]tese|endopr[oô]tese)\b",
     "OPME"),
    
    (r"\bopme|materiais|canula\b", "OPME"),

    
    (r"\b(ans|nip)\b", "Judiciais + NIPs"),
]

def route_by_keywords(text: str) -> str | None:
    for pattern, setor in KEYWORD_SECTOR_RULES:
        if re.search(pattern, text, flags=re.I):
            return setor
    return None


FINANCE_OVERRIDE_RULES: list[tuple[str, str]] = [
    
    (r"\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|"
     r"glosa[s]?|demonstrativo[s]?|portal\s+sa[úu]de\s+caixa|xml)\b",
     "Faturamento"),

    
    (r"\b(nota[s]?\s+fiscal(?:is)?|issqn|inss|cadastro\s+tribut[áa]rio|"
     r"imposto[s]?|prestador(?:es)?)\b",
     "Financeiro / Tributos"),
]

def override_finance(text: str) -> str | None:
    for pattern, setor in FINANCE_OVERRIDE_RULES:
        if re.search(pattern, text, flags=re.I):
            return setor
    return None
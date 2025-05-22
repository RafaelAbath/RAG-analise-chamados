import re

KEYWORD_SECTOR_RULES: list[tuple[str, str]] = [
    # 1️⃣ Primeiro: ANS / NIP → Judiciais + NIPs
    (r"(?i)\b(ans|nip)\b", "Judiciais + NIPs"),

    # 2️⃣ Depois: OPME + Reclame / Judicial
    (r"\b(opme)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(opme)\b",
     "NIP Reclames e judiciais OPME"),

    # 3️⃣ Home Care + Reclame / Judicial
    (r"\b(home\s*care|hc)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(home\s*care|hc)\b",
     "NIP Reclames e judiciais HC"),

    # 4️⃣ Garantia de Atendimento (contato + whatsapp)
    (r"(?i)(?=.*\bcontato\b)(?=.*\bwhatsapp\b)",
     "Garantia de Atendimento (Busca de rede)"),

    # 5️⃣ Padrões OPME gerais
    (r"(?i)\b(cpap|aparelho|lente|catarata|pr[oô]tese|endopr[oô]tese|materiais|canula)\b",
     "OPME"),
]

FINANCE_OVERRIDE_RULES: list[tuple[str, str]] = [
    (r"(?i)\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|"
     r"glosa[s]?|demonstrativo[s]?|portal\s+sa[úu]de\s+caixa|xml)\b",
     "Faturamento"),
    (r"(?i)\b(nota[s]?\s+fiscal(?:is)?|issqn|inss|cadastro\s+tribut[áa]rio|"
     r"imposto[s]?|prestador(?:es)?)\b",
     "Financeiro / Tributos"),
]
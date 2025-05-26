import re

KEYWORD_SECTOR_RULES: list[tuple[str, str]] = [
    
    (r"(?i)\b(medicamento|dosagem|medicação|comprimido)\b", "Medicamento"),

    (r"(?i)\bsolicita(?:r|ção\s+de)\s+reembolso\b", "Reembolso"),

    (r"(?i)\b(nota[s]?\s+fiscal(?:is)?|issqn|inss|cadastro\s+tribut[áa]rio|"
     r"imposto[s]?|prestador(?:es)?)\b",
     "Financeiro / Tributos"),

    (r"(?i)\b(ans|nip)\b", "Judiciais + NIPs"),

    
    (r"\b(opme)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(opme)\b",
     "NIP Reclames e judiciais OPME"),

    
    (r"\b(home\s*care|hc)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(home\s*care|hc)\b",
     "NIP Reclames e judiciais HC"),

    
    (r"(?i)(?=.*\bcontato\b)(?=.*\bwhatsapp\b)",
     "Garantia de Atendimento (Busca de rede)"),
    
    (r"(?i)\b(cpap|aparelho|lente|catarata|pr[oô]tese|endopr[oô]tese|materiais|canula)\b",
     "OPME"),

     
    (r"(?i)\b(autoriz[ao]ção previa?|cobertura|junta\s+m[eé]dica|passagem\s+de\s+gastrostom\w+|"
    r"solicita(?:ç(?:a|ã)o)?\s+(?:de\s+)?(procedimento|exame|internaç(?:a|ão)))\b",
    "Autorização"),
]

FINANCE_OVERRIDE_RULES: list[tuple[str, str]] = [
    # 🔹 PRIORIDADE 1 — documentos fiscais
    (r"(?i)\b(nota[s]?\s+fiscal(?:is)?|issqn|inss|cadastro\s+tribut[áa]rio|"
     r"imposto[s]?|prestador(?:es)?|xml\s+nf[e]?)\b",
     "Financeiro / Tributos"),

    # 🔸 PRIORIDADE 2 — itens de cobrança interna
    (r"(?i)\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|"
     r"glosa[s]?|demonstrativo[s]?|portal\s+sa[úu]de\s+caixa)\b",
     "Faturamento"),
]
import re
from typing import List, Tuple, Dict

AUTHORIZATION_RULES: List[Tuple[str, str]] = [
    # Home Care
    (r"(?i)\b(domiciliar|internação\s+domiciliar|home\s*care|hc)\b",                 "Home Care"),

    # Medicamento / Quimioterapia
    (r"(?i)\b(medicamento|dosagem|medicação|comprimido|quimioterapia)\b",            "Medicamento"),

    # OPME (materiais / próteses)
    (r"(?i)\b(cpap|aparelho|lente|catarata|pr[oô]tese|endopr[oô]tese|materiais|cânula)\b",
                                                                                    "OPME"),

    # Solicitação de procedimento / exame / internação
    (r"(?i)\b(autoriz[ao]ção\s+prévia?|cobertura|junta\s+m[eé]dica|"
     r"passagem\s+de\s+gastrostom\w+|solicita(?:ç[ãa]o)?\s+(?:de\s+)?"
     r"(procedimento|exame|internaç[ãa]o))\b",                                       "Autorização"),
]

# 2) COLLECTION: nips  ------------------------------------------------------
NIPS_RULES: List[Tuple[str, str]] = [
    # Reclamações / NIPs gerais
    (r"(?i)\b(ans|nip)\b",                                                          "Judiciais + NIPs"),

    # Reclamações OPME
    (r"(?i)\b(opme)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(opme)\b",                               "NIP Reclames e judiciais OPME"),

    # Reclamações Home Care
    (r"(?i)\b(home\s*care|hc)\b.*\b(nip|ans|judicial|reclame)s?\b"
     r"|\b(nip|ans|judicial|reclame)s?\b.*\b(home\s*care|hc)\b",                     "NIP Reclames e judiciais HC"),
]

# 3) COLLECTION: reembolso  --------------------------------------------------
REEMB_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(solicita(?:r|ção\s+de)\s+reembolso|reembolso\s+integral|"
     r"anali[sz]e\s+de\s+reembolso\s+integral|reembolso)\b",                        "Reembolso"),
]

# 4) COLLECTION: financeiros  ------------------------------------------------
FINANCEIROS_RULES: List[Tuple[str, str]] = [
    # Documentos fiscais – vai para Financeiro / Tributos
    (r"(?i)\b(nota[s]?\s+fiscal(?:is)?|issqn|inss|cadastro\s+tribut[áa]rio|"
     r"imposto[s]?|prestador(?:es)?|xml\s+nf[e]?)\b",                               "Financeiro / Tributos"),

    # Itens de faturamento interno
    (r"(?i)\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|"
     r"glosa[s]?|demonstrativo[s]?|portal\s+sa[úu]de\s+caixa)\b",                   "Faturamento"),
]

# 5) COLLECTION: geral  ------------------------------------------------------
GERAL_RULES: List[Tuple[str, str]] = [
    
    (r"(?i)(?=.*\bcontato\b)(?=.*\bwhatsapp\b)|"
     r"\bbenefici[áa]ria\s+entrou\s+em\s+contato\s+solicitando\s+informa(?:ç|c)ão\b|"
     r"\binformar\s+sobre\b",                                                       "Garantia de Atendimento (Busca de rede)"),
]


COLLECTION_RULES: Dict[str, List[Tuple[str, str]]] = {
    "authorization_geral": AUTHORIZATION_RULES,
    "nips":                NIPS_RULES,
    "reembolso":           REEMB_RULES,
    "financeiros":         FINANCEIROS_RULES,
    "geral":               GERAL_RULES,
}


FINANCE_OVERRIDE_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|"
     r"glosa[s]?|demonstrativo[s]?|portal\s+sa[úu]de\s+caixa)\b",                   "Faturamento"),
]

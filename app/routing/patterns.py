import re
from typing import List, Tuple, Dict


AUTHORIZATION_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(domiciliar|internação\s+domiciliar|home\s*care|hc)\b",                                "Home Care"),
    (r"(?i)\b(medicamento|dosagem|medicação|comprimido|quimioterapia)\b",                           "Medicamento"),
    (r"(?i)\b(cpap|aparelho|lente|catarata|pr[oô]tese|endopr[oô]tese|materiais|cânula)\b",          "OPME"),
    (r"(?i)\b(autoriz[ao]ção\s+prévia?|cobertura|junta\s+m[eé]dica|passagem\s+de\s+gastrostom\w+|"
     r"solicita(?:ç[ãa]o)?\s+(?:de\s+)?(procedimento|exame|internaç[ãa]o))\b",                      "Autorização"),
]

NIPS_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(ans|nip)\b",                                                                          "Judiciais + NIPs"),
    (r"(?i)\b(opme)\b.*\b(nip|ans|judicial|reclame)s?\b|\b(nip|ans|judicial|reclame)s?\b.*\b(opme)\b",
                                                                                                    "NIP Reclames e judiciais OPME"),
    (r"(?i)\b(home\s*care|hc)\b.*\b(nip|ans|judicial|reclame)s?\b|\b(nip|ans|judicial|reclame)s?\b.*\b(home\s*care|hc)\b",
                                                                                                    "NIP Reclames e judiciais HC"),
]

REEMB_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(solicita(?:r|ção\s+de)\s+reembolso|reembolso\s+integral|anali[sz]e\s+de\s+reembolso\s+integral|reembolso)\b",
                                                                                                    "Reembolso"),
]

FINANCEIROS_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(nota[s]?\s+fiscal(?:is)?|issqn|inss|cadastro\s+tribut[áa]rio|imposto[s]?|prestador(?:es)?|xml\s+nf[e]?)\b",
                                                                                                    "Financeiro / Tributos"),
    (r"(?i)\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|glosa[s]?|demonstrativo[s]?|portal\s+sa[úu]de\s+caixa)\b",
                                                                                                    "Faturamento"),
]

GERAL_RULES: List[Tuple[str, str]] = [
    (r"(?i)(?=.*\bcontato\b)(?=.*\bwhatsapp\b)|\bbenefici[áa]ria\s+entrou\s+em\s+contato\s+solicitando\s+informa(?:ç|c)ão\b|\binformar\s+sobre\b",
                                                                                                    "Garantia de Atendimento (Busca de rede)"),
]

ODONTO_REEMB_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(reembolso(?:s)?\s*(?:odontol[oó]gic[oa]s?)?|nip[s]?|reclame|judicial)\b",             "Odonto Reembolso"),
]

ODONTO_FAT_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(nota[s]?\s+fiscal(?:is)?\s*(?:odontol[oó]gic[oa]s?)?|glosa[s]?|cobranç?as?|demonstrativo[s]?|coparticipa(?:ç[aã]o)?)\b",
                                                                                                    "Odonto Faturamento"),
]

ODONTO_AUTO_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(guia[s]?|sadt|internação|autoriz[aç][ãa]o|cobertura|rol\s+ans|tratamento|cirurgia)\b",
                                                                                                    "Odonto Autorização"),
]

ODONTO_RULES: List[Tuple[str, str]] = ODONTO_REEMB_RULES + ODONTO_FAT_RULES + ODONTO_AUTO_RULES



COLLECTION_RULES: Dict[str, List[Tuple[str, str]]] = {
    "authorization_geral": AUTHORIZATION_RULES,
    "nips":                NIPS_RULES,
    "reembolso":           REEMB_RULES,
    "financeiros":         FINANCEIROS_RULES,
    "geral":               GERAL_RULES,
    "odontologia":         ODONTO_RULES,
}



FINANCE_OVERRIDE_RULES: List[Tuple[str, str]] = [
    (r"(?i)\b(benefici[áa]rio[sc]?|coparticipa(?:ç[aã]o)?|peg(?:s)?|glosa[s]?|demonstrativo[s]?|portal\s+sa[úu]de\s+caixa)\b",
                                                                                                    "Faturamento"),
]

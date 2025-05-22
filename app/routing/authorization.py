import re
from typing import Optional


AUTH_PATTERNS = [
    (r"\b(autorizacao previa|pedido de autorizacao)\b", "Autorização"),
    (r"\b(cpap|aparelho|lente|catarata|pr[oô]tese)\b", "OPME"),
    (r"(?i)(?=.*\bcontato\b)(?=.*\bwhatsapp\b)", "Garantia de Atendimento (Busca de rede)"),
    (r"\b(medicamento)\b", "Medicamento"),
]

def override_autorizacao(text: str) -> Optional[str]:
    for pattern, setor in AUTH_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            return setor
    return None
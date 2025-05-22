# app/routing/authorization.py
import re
from typing import Optional
from routing.base import Router
from core.sector_meta import allowed_sectors

# Padrões específicos para refinar dentro de "autorizacao_geral"
AUTH_PATTERNS = [
    (r"\b(autorizacao previa|pedido de autorizacao)\b", "Autorização"),
    (r"\b(cpap|aparelho|lente|catarata|pr[oô]tese)\b", "OPME"),
    (r"(?i)(?=.*\bcontato\b)(?=.*\bwhatsapp\b)", "Garantia de Atendimento (Busca de rede)"),
    (r"\b(medicamento)\b", "Medicamento"),
]

def override_autorizacao(text: str) -> Optional[str]:
    for pattern, setor in AUTH_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            return next((s for s in allowed_sectors if s == setor), setor)
    return None

import re
from typing import Optional
from core.models import Chamado
from routing.base import Router
from routing.patterns import KEYWORD_SECTOR_RULES, FINANCE_OVERRIDE_RULES

COMBINED_KEYWORD_RULES = FINANCE_OVERRIDE_RULES + KEYWORD_SECTOR_RULES

class KeywordRouter(Router):
    def _route(self, chamado: Chamado) -> Optional[str]:
        text = f"{chamado.protocolo} {chamado.descricao}"
        for pattern, setor in KEYWORD_SECTOR_RULES:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return setor
        return None

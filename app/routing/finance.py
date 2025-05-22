import re
from typing import Optional
from routing.patterns import FINANCE_OVERRIDE_RULES


def override_finance(text: str) -> Optional[str]:
    txt = text.lower()
    for pattern, setor in FINANCE_OVERRIDE_RULES:
        if re.search(pattern, txt, flags=re.I):
            return setor
    return None



from core.models import Chamado
from routing.base import Router

class FinanceOverrideRouter(Router):
    def _route(self, chamado: Chamado) -> Optional[str]:
        return override_finance(f"{chamado.titulo} {chamado.descricao}")
import re
from typing import Optional
from routing.patterns import FINANCE_OVERRIDE_RULES


def override_finance(setor_atual: str, text: str) -> tuple[str, str | None]:
    for pattern, setor in FINANCE_OVERRIDE_RULES:
        if re.search(pattern, text, flags=re.I) and setor != setor_atual:
            return setor, "finance_override"
    return setor_atual, None





from core.models import Chamado
from routing.base import Router

class FinanceOverrideRouter(Router):
    def _route(self, chamado: Chamado) -> Optional[str]:
        return override_finance(f"{chamado.protocolo} {chamado.descricao}")
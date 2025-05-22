import re
from typing import Optional
from core.models import Chamado
from routing.patterns import FINANCE_OVERRIDE_RULES
from routing.base import Router

class FinanceOverrideRouter(Router):
    def _route(self, chamado: Chamado) -> Optional[str]:
        text = f"{chamado.titulo} {chamado.descricao}".lower()
        for pattern, setor in FINANCE_OVERRIDE_RULES:
            if re.search(pattern, text, flags=re.I):
                return setor
        return None

# app/routing/__init__.py
from routing.keywords import KeywordRouter
from routing.finance import FinanceOverrideRouter
from routing.llm import LLMRouter

# Monta a corrente de roteamento
router_chain = KeywordRouter(
    FinanceOverrideRouter(
        LLMRouter()
    )
)
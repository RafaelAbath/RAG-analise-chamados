import re
from typing import Optional
from core.models import Chamado
from routing.base import Router
from routing.patterns import KEYWORD_SECTOR_RULES

class KeywordRouter(Router):
    """Busca direta por palavra-chave; se casar, devolve setor e marca proveniência."""

    def _route(self, chamado: Chamado) -> Optional[str]:
        text = f"{chamado.protocolo} {chamado.descricao}"
        for pattern, setor in KEYWORD_SECTOR_RULES:
            if re.search(pattern, text, flags=re.I):
                chamado.proveniencia = "keyword"
                return setor          # encerra a corrente aqui
        return None                   # segue para o próximo router

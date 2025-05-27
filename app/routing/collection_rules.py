import re
from typing import Optional
from core.models import Chamado
from routing.base import Router
from routing.patterns import COLLECTION_RULES  

class CollectionRuleRouter(Router):
    def _route(self, chamado: Chamado) -> Optional[str]:
        coll = getattr(chamado, "collection", None)
        if not coll:
            return None

        text = f"{chamado.protocolo} {chamado.descricao}"
        for pattern, setor in COLLECTION_RULES.get(coll, []):
            if re.search(pattern, text, flags=re.I):
                chamado.proveniencia = "collection_rule"
                return setor
        return None

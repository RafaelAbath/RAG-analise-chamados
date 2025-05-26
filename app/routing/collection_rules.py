# routing/collection_rules.py
from routing.base import Router
import re
from routing.patterns import FINANCE_OVERRIDE_RULES, KEYWORD_SECTOR_RULES
COLLECTION_RULES = {
    "financeiros": FINANCE_OVERRIDE_RULES,
    "authorization_geral": KEYWORD_SECTOR_RULES,   # exemplo – ajuste conforme precisar
    # …adicione aqui outras collections
}

class CollectionRuleRouter(Router):
    def _route(self, chamado):
        coll = getattr(chamado, "collection", None)
        if not coll:
            return None
        text = f"{chamado.protocolo} {chamado.descricao}"
        for pattern, setor in COLLECTION_RULES.get(coll, []):
            if re.search(pattern, text, flags=re.I):
                return setor
        return None

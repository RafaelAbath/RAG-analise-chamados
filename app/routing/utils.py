from routing.patterns import COLLECTION_RULES, FINANCE_OVERRIDE_RULES
from typing import Optional, List

def get_allowed_sectors() -> list[str]:
    sectors = [
        setor
        for rules in COLLECTION_RULES.values()
        for _, setor in rules
    ]
    
    sectors += [setor for _, setor in FINANCE_OVERRIDE_RULES]
    seen = set()
    allowed = []
    for s in sectors:
         if s not in seen:
             seen.add(s)
             allowed.append(s)
    return allowed

def clean_setor(raw: str, allowed: Optional[List[str]] = None) -> str:
    text = raw.strip()
    if allowed:
        # 1) match exato (case-insensitive)
        for opt in allowed:
            if text.lower() == opt.lower():
                return opt
        # 2) match parcial
        for opt in allowed:
            if opt.lower() in text.lower():
                return opt
        # 3) fallback para o primeiro permitido
        return allowed[0]
    return text
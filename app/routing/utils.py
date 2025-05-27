from routing.patterns import COLLECTION_RULES, FINANCE_OVERRIDE_RULES

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

def clean_setor(raw: str) -> str:

    text = raw.strip().strip('"').strip("'")
    for sector in get_allowed_sectors():
        if text.lower() == sector.lower():
            return sector
    for sector in get_allowed_sectors():
        if text.lower() in sector.lower():
            return sector
    return text

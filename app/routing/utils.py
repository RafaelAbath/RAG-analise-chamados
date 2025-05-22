from routing.patterns import (
    KEYWORD_SECTOR_RULES,
    FINANCE_OVERRIDE_RULES,
)
from routing.authorization import AUTH_PATTERNS

def get_allowed_sectors() -> list[str]:
    sectors = []
    sectors += [sector for _, sector in KEYWORD_SECTOR_RULES]
    sectors += [sector for _, sector in FINANCE_OVERRIDE_RULES]
    sectors += [sector for _, sector in AUTH_PATTERNS]

    seen = set()
    allowed = []
    for s in sectors:
        if s not in seen:
            seen.add(s)
            allowed.append(s)
    return allowed

import re
import unicodedata
from difflib import get_close_matches
from typing import List, Optional

def clean_setor(raw: str) -> str:
    return raw.split(":", 1)[1].strip() if ":" in raw else raw.strip()

def normalize_text(raw: str) -> str:
    norm = unicodedata.normalize('NFKD', raw)
    norm = norm.encode('ascii', 'ignore').decode('ascii').lower()
    norm = re.sub(r'[^a-z0-9\s]', ' ', norm)
    return norm

def get_best_match(raw: str, choices: List[str], cutoff: float = 0.6) -> Optional[str]:
    matches = get_close_matches(raw, choices, n=1, cutoff=cutoff)
    return matches[0] if matches else None

import pandas as pd
from typing import Dict

_df_meta = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
_required = {"Setor", "Responsabilidades", "Exemplos"}
_missing = _required - set(_df_meta.columns)
if _missing:
    raise RuntimeError(f"Colunas faltando no CSV: {_missing}")

sector_info: Dict[str, Dict[str, str]] = {
    row["Setor"]: {
        "responsabilidades": str(row["Responsabilidades"]).strip(),
        "exemplos": str(row["Exemplos"]).strip()
    }
    for _, row in _df_meta.iterrows()
}

allowed_sectors = list(sector_info.keys())
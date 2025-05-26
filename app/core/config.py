from pydantic_settings import BaseSettings
import re
from pathlib import Path

class Settings(BaseSettings):
    API_KEY:           str
    OPENAI_API_KEY:    str
    EMBEDDING_MODEL:   str
    FINETUNED_MODEL:   str

    QDRANT_URL:        str
    QDRANT_API_KEY:    str

    QDRANT_COLL_AUTH:  str   
    QDRANT_COLL_NIPS:  str   
    QDRANT_COLL_FIN:   str   
    QDRANT_COLL_REEMB: str   
    QDRANT_COLL_ODO:   str   
    QDRANT_COLL_GERAL: str   

    FAT_BRUTO_CNPJ_FILE: Path
    class Config:
        env_file = ".env"
        env_prefix = ""


    @property
    def CNPJS_FAT_BRUTO(self) -> set[str]:
        p = Path(self.FAT_BRUTO_CNPJ_FILE).expanduser().resolve()
        if not p.exists():
            return set()
        raw = p.read_text(encoding="utf-8").splitlines()
        return {re.sub(r"\D", "", line) for line in raw if line.strip()}


settings = Settings()

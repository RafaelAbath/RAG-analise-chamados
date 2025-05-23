from pydantic_settings import BaseSettings
import re
from pathlib import Path

class Settings(BaseSettings):
    QDRANT_COLLECTION_NIP: str = "nip_reclames"
    QDRANT_COLLECTION: str     = "tecnicos"
    QDRANT_COLLECTION_AUT: str = "autorizacao_geral"
    OPENAI_API_KEY: str
    FINETUNED_MODEL: str
    EMBEDDING_MODEL: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    API_KEY: str
    FAT_BRUTO_CNPJ_FILE: str = "data/fat_bruto_cnpjs.txt"

    class Config:
        env_file = ".env"

    @property
    def CNPJS_FAT_BRUTO(self) -> set[str]:
        p = Path(self.FAT_BRUTO_CNPJ_FILE).expanduser().resolve()
        if not p.exists():
            return set()
        raw = p.read_text(encoding="utf-8").splitlines()
        return {re.sub(r"\D", "", line) for line in raw if line.strip()}


settings = Settings()

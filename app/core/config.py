from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    QDRANT_COLLECTION_NIP: str = "nip_reclames"
    QDRANT_COLLECTION: str = "tecnicos"
    QDRANT_COLLECTION_AUT: str = "autorizacao_geral"
    OPENAI_API_KEY: str
    FINETUNED_MODEL: str
    EMBEDDING_MODEL: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
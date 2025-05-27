from routing.base import Router
from services.collection_mapper import ALL_COLLECTIONS
from core.config import settings
from openai import OpenAI
from qdrant_client import QdrantClient


class CollectionRouter(Router):
    def __init__(self, successor=None):
        super().__init__(successor)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(url=settings.QDRANT_URL,
                                   api_key=settings.QDRANT_API_KEY)

    def _route(self, chamado):
        vec = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=f"{chamado.protocolo} {chamado.descricao}"
        ).data[0].embedding

        best = None
        for coll in ALL_COLLECTIONS:
            res = self.qdrant.search(coll, vec, limit=1)
            if res and (best is None or res[0].score > best[0].score):
                best = (res[0], coll)
        if best:
            chamado.collection = best[1]       
        return None

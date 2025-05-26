from typing import List

from core.config import settings
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from services.collection_mapper import collection_for


ALL_COLLECTIONS: List[str] = [
    settings.QDRANT_COLL_AUTH,
    settings.QDRANT_COLL_NIPS,
    settings.QDRANT_COLL_FIN,
    settings.QDRANT_COLL_REEMB,
    settings.QDRANT_COLL_ODO,
    settings.QDRANT_COLL_GERAL,
]

class TechSelector:
    def __init__(self):
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(url=settings.QDRANT_URL,
                                   api_key=settings.QDRANT_API_KEY)

    def select(self, setor: str, chamado) -> dict:
        texto = f"{getattr(chamado, 'protocolo', '')} {chamado.descricao}"
        vec = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texto
        ).data[0].embedding

        primary    = collection_for(setor)
        candidates = [primary] + [
            settings.QDRANT_COLL_AUTH,
            settings.QDRANT_COLL_NIPS,
            settings.QDRANT_COLL_FIN,
            settings.QDRANT_COLL_REEMB,
            settings.QDRANT_COLL_ODO,
            settings.QDRANT_COLL_GERAL,
 ]

        hit        = None
        used_coll  = None
        for coll in candidates:
            res = self.qdrant.search(
                collection_name=coll,
                query_vector=vec,
                limit=1,
                with_payload=True,
                query_filter=Filter(
                    must=[FieldCondition(key="setor",
                                         match=MatchValue(value=setor))]
                ),
            )
            if res:
                hit, used_coll = res[0], coll
                break

        if hit is None:
            raise RuntimeError(f"Nenhum técnico encontrado para o setor “{setor}”")

        p = hit.payload
        return {
            "setor_ia":          setor,
            "tecnico_id":        hit.id,
            "tecnico_nome":      p["nome"],
            "tecnico_setor":     p["setor"],
            "responsabilidades": p.get("responsabilidades"),
            "exemplos":          p.get("exemplos"),
            "confianca":         hit.score,
            "collection":        used_coll,  
        }

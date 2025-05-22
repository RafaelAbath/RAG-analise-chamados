from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from core.config import settings

class TechSelector:
    def __init__(self):
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )

    def select(self, setor: str, chamado) -> dict:
        
        txt = f"{chamado.titulo} {chamado.descricao}"
        vec = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding

       
        coll = settings.QDRANT_COLLECTION  

        
        hits = self.qdrant.search(
            collection_name=coll,
            query_vector=vec,
            limit=1,
            with_payload=True,
            query_filter=Filter(must=[
                FieldCondition(key="setor", match=MatchValue(value=setor))
            ])
        )
        if not hits:
            raise RuntimeError(f"Nenhum técnico encontrado para o setor {setor}")

        hit = hits[0]
        p = hit.payload
        
        return {
            "setor_ia": setor,
            "tecnico_id": hit.id,
            "tecnico_nome": p["nome"],
            "tecnico_setor": p["setor"],
            "responsabilidades": p.get("responsabilidades"),
            "exemplos": p.get("exemplos"),
            "confianca": hit.score
        }

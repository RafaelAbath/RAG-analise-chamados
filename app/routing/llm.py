# app/services/tech_selector.py
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from core.config import settings
from routing.utils import collection_for  # assume você centralizou a lógica aqui

class TechSelector:
    """
    Seleciona o técnico mais adequado para um chamado, buscando primeiro na coleção específica do setor,
    e em seguida realizando busca global caso não haja resultados.
    """
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def select(self, setor: str, chamado) -> dict:
        # Gera embedding apenas do chamado
        txt = f"{chamado.titulo}. {chamado.descricao}"
        vec = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding

        # 1) Tenta na coleção específica do setor
        coll = collection_for(setor, chamado.classificacao)
        hits = self.client.search(
            collection_name=coll,
            query_vector=vec,
            limit=1,
            with_payload=True,
            query_filter=Filter(must=[
                FieldCondition(key="setor", match=MatchValue(value=setor))
            ])
        )

        if hits:
            hit = hits[0]
            final_setor = setor
        else:
            # 2) Busca global em todas as coleções sem filtro de setor
            best = None
            for c in (
                settings.QDRANT_COLLECTION,
                settings.QDRANT_COLLECTION_NIP,
                settings.QDRANT_COLLECTION_AUT,
            ):
                candidate = self.client.search(
                    collection_name=c,
                    query_vector=vec,
                    limit=1,
                    with_payload=True
                )
                if candidate:
                    if not best or candidate[0].score > best.score:
                        best = candidate[0]
            if not best:
                raise RuntimeError(f"Nenhum técnico encontrado para o setor {setor}")
            hit = best
            final_setor = hit.payload.get("setor", setor)

        payload = hit.payload
        return {
            "setor_ia": final_setor,
            "tecnico_id": hit.id,
            "tecnico_nome": payload.get("nome"),
            "tecnico_setor": payload.get("setor"),
            "confianca": hit.score,
        }

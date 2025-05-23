from core.config import settings
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

def collection_for(setor: str, classificacao: str | None) -> str:
    s = setor.lower()
    if classificacao and classificacao.lower() == "autorizacao_geral":
        return settings.QDRANT_COLLECTION_AUT
    if setor in (
        "Autorização",
        "Medicamento",
        "OPME",
        "Garantia de Atendimento (Busca de rede)",
    ):
        return settings.QDRANT_COLLECTION_AUT
    if any(k in s for k in ("nip", "ans", "judicial", "reclame")):
        return settings.QDRANT_COLLECTION_NIP
    return settings.QDRANT_COLLECTION

class TechSelector:
    def __init__(self):
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )

    def select(self, setor: str, chamado) -> dict:
        
        txt = f"{chamado.protocolo} {chamado.descricao}"
        vec = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding

        
        primary = collection_for(setor, chamado.classificacao)
        candidates = [primary] + [
            c for c in (
                settings.QDRANT_COLLECTION_AUT,
                settings.QDRANT_COLLECTION_NIP,
                settings.QDRANT_COLLECTION
            ) if c != primary
        ]

        
        used_coll = None
        hits = None
        for coll in candidates:
            hits = self.qdrant.search(
                collection_name=coll,
                query_vector=vec,
                limit=3,
                with_payload=True,
                query_filter=Filter(must=[
                    FieldCondition(key="setor", match=MatchValue(value=setor))
                ])
            )
            if hits:
                used_coll = coll
                break

        if not hits:
            raise RuntimeError(f"Nenhum técnico encontrado para o setor {setor}")

        hit = hits[0]
        p = hit.payload
        return {
            "setor_ia":        setor,
            "tecnico_id":      hit.id,
            "tecnico_nome":    p["nome"],
            "tecnico_setor":   p["setor"],
            "responsabilidades": p.get("responsabilidades"),
            "exemplos":        p.get("exemplos"),
            "confianca":       hit.score,
            "collection":      used_coll
        }

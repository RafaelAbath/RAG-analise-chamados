from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from core.config import settings
from services.tech_selector import collection_for  # <-- importe aqui

class TechSelector:
    def __init__(self):
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )

    def select(self, setor: str, chamado) -> dict:
        # 1) Gera embedding do chamado
        txt = f"{chamado.titulo} {chamado.descricao}"
        vec = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding

        # 2) Escolhe a collection com base no setor e classificação
        coll = collection_for(setor, chamado.classificacao)

        # 3) Busca o técnico mais próximo nessa collection
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

def collection_for(setor: str, classificacao: str | None) -> str:
    s = setor.lower()
    # 1) Autorização geral explícita
    if classificacao and classificacao.lower() == "autorizacao_geral":
        return settings.QDRANT_COLLECTION_AUT

    # 2) Setores que vivem em autorizacao_geral
    if setor in (
        "Autorização",
        "Medicamento",
        "OPME",
        "Garantia de Atendimento (Busca de rede)",
    ):
        return settings.QDRANT_COLLECTION_AUT

    # 3) NIP / Reclame / Judicial
    if any(k in s for k in ("nip", "reclame", "judicial")):
        return settings.QDRANT_COLLECTION_NIP

    # 4) Resto → coleção default
    return settings.QDRANT_COLLECTION

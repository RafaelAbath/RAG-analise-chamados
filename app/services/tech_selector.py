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

    def select(self, setor: str, chamado, info: dict):
        # info contém chaves 'responsabilidades' e 'exemplos'
        txt = (
            f"Responsabilidades: {info['responsabilidades']}. "
            f"Exemplos: {info['exemplos']}. "
            f"Chamado: {chamado.titulo}. {chamado.descricao}"
        )
        vec = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding
        collection = None
        # decide coleção conforme setor
        low = setor.lower()
        if setor == settings.FINETUNED_MODEL:
            collection = settings.QDRANT_COLLECTION_AUT
        elif any(k in low for k in ("nip","ans","judicial","reclame")):
            collection = settings.QDRANT_COLLECTION_NIP
        elif setor in ("Autorização","Medicamento","OPME","Garantia de Atendimento (Busca de rede)"):
            collection = settings.QDRANT_COLLECTION_AUT
        else:
            collection = settings.QDRANT_COLLECTION

        hits = self.qdrant.search(
            collection_name=collection,
            query_vector=vec,
            limit=1,
            with_payload=True,
            query_filter=Filter(must=[FieldCondition(key="setor", match=MatchValue(value=setor))]),
        )
        if not hits:
            raise RuntimeError(f"Nenhum técnico encontrado para o setor {setor}")

        hit = hits[0]
        return {
            "setor_ia": setor,
            "tecnico_id": hit.id,
            "tecnico_nome": hit.payload["nome"],
            "tecnico_setor": hit.payload["setor"],
            "confianca": hit.score,
        }

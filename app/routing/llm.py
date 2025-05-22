from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from routing.base import Router
from routing.utils import get_allowed_sectors, clean_setor
from core.config import settings

class LLMRouter(Router):
    def __init__(self, successor=None):
        super().__init__(successor)
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.allowed_sectors = get_allowed_sectors()

    def _route(self, chamado):
        # 1) Embedding do chamado
        txt = f"{chamado.protocolo} {chamado.descricao}"
        vec = self.llm.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding

        # 2) Busca nos vetores (usando .search para permanecer compatível)
        collections = [
            settings.QDRANT_COLLECTION,
            settings.QDRANT_COLLECTION_AUT,
            settings.QDRANT_COLLECTION_NIP,
        ]
        neighbors = []
        for coll in collections:
            hits = self.qdrant.search(
                collection_name=coll,
                query_vector=vec,    # .search aceita query_vector
                limit=3,
                with_payload=True,
            )
            neighbors.extend(hits)

        # 3) Monta um pequeno sumário dos vizinhos
        resumo = "\n".join(
            f"- {p.payload['nome']} ({p.payload['setor']}) [score: {p.score:.2f}]"
            for p in neighbors
        )

        # 4) Prompt para a LLM, incluindo o resumo
        system_msg = (
            "Você é um roteador de chamados. Abaixo estão os 3 técnicos mais próximos "
            "encontrados pelo Qdrant para este chamado:\n"
            f"{resumo}\n\n"
            "Com base nisso e na descrição, responda **apenas** com UM dos setores válidos:\n"
            + ", ".join(self.allowed_sectors)
        )
        user_msg = f"Título: {chamado.protocolo}\nDescrição: {chamado.descricao}"

        resp = self.llm.chat.completions.create(
            model=settings.FINETUNED_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg}
            ],
            temperature=0.0
        )

        # 5) Limpa e devolve só o setor
        return clean_setor(resp.choices[0].message.content.strip())

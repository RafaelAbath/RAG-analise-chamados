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
        
        txt = f"{chamado.protocolo} {chamado.descricao}"
        vec = self.llm.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding

        
        collections = [
            settings.QDRANT_COLL_AUTH,    
            settings.QDRANT_COLL_NIPS,    
            settings.QDRANT_COLL_GERAL,   
        ]
        neighbors = []
        for coll in collections:
            hits = self.qdrant.search(
                collection_name=coll,
                query_vector=vec,    
                limit=3,
                with_payload=True,
            )
            neighbors.extend(hits)

        
        resumo = "\n".join(
            f"- {p.payload['nome']} ({p.payload['setor']}) [score: {p.score:.2f}]"
            for p in neighbors
        )

        
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

        
        return clean_setor(resp.choices[0].message.content.strip())

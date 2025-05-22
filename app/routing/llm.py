from collections import Counter
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from routing.base import Router
from routing.utils import get_allowed_sectors, clean_setor
from core.config import settings

class LLMRouter(Router):
    def __init__(self):
        super().__init__()
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.allowed_sectors = get_allowed_sectors()

    def _route(self, chamado):
        # 1) chama a LLM para obter um setor inicial
        system_msg = (
            "Você é um roteador de chamados. Responda APENAS com um dos setores válidos:\n"
            + ", ".join(self.allowed_sectors)
        )
        user_msg = f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}"
        resp = self.llm.chat.completions.create(
            model=settings.FINETUNED_MODEL,
            messages=[{"role":"system", "content":system_msg},
                      {"role":"user",   "content":user_msg}],
            temperature=0.0
        )
        llm_sector = clean_setor(resp.choices[0].message.content.strip())

        # 2) gera embedding e busca no Qdrant sem filtro de setor
        txt = f"{chamado.titulo} {chamado.descricao}"
        vec = self.llm.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=txt
        ).data[0].embedding

        hits = self.qdrant.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=vec,
            limit=5,
            with_payload=True
        )

        # 3) obtém o setor mais comum entre os top 5 resultados
        if hits:
            freq = Counter(h.payload["setor"] for h in hits)
            qdrant_sector, _ = freq.most_common(1)[0]
        else:
            qdrant_sector = None

        # 4) decide: dá preferência ao Qdrant, mas faz fallback para a LLM
        final = qdrant_sector or llm_sector
        return final

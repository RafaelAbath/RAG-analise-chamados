from openai import OpenAI
from qdrant_client import QdrantClient
from typing import Optional

from routing.base import Router
from services.collection_mapper import ALL_COLLECTIONS
from core.config import settings

MIN_SCORE: float = 0.30   
BOOST_ODONTO: float = 0.10  


class CollectionRouter(Router):
    def __init__(self, successor: Optional[Router] = None) -> None:
        super().__init__(successor)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )

    
    def _route(self, chamado):  
        text = f"{chamado.protocolo} {chamado.descricao}".lower()

      
        vec = (
            self.openai.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
            )
            .data[0]
            .embedding
        )

        
        best_score = 0.0
        best_coll: Optional[str] = None

        for coll in ALL_COLLECTIONS:
            res = self.qdrant.search(coll, vec, limit=1)
            if not res:
                continue

            score = res[0].score

           
            if "odonto" in text and coll == settings.QDRANT_COLL_ODO:
                score += BOOST_ODONTO

            if score > best_score:
                best_score, best_coll = score, coll

        
        if best_coll and best_score >= MIN_SCORE:
            chamado.collection = best_coll

        
        return None
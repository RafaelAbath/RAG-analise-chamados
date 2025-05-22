# app/api/main.py
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader

from core.config import settings
from core.models import Chamado, Resposta, RespostaDebug
from routing import router_chain
from routing.finance import override_finance
from routing.authorization import override_autorizacao
from services.tech_selector import TechSelector, collection_for

app = FastAPI(title="API de RAG para Chamados")
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

def get_api_key(key: str = Depends(api_key_header)):
    if key != settings.API_KEY:
        raise HTTPException(401, "Chave de API inválida ou ausente")
    return key

selector = TechSelector()

@app.post("/classify/", response_model=Resposta, dependencies=[Depends(get_api_key)])
async def classify_and_assign(chamado: Chamado):
    text = f"{chamado.titulo} {chamado.descricao}".lower()

    # 1) Roteamento por palavras-chave
    setor = router_chain.handle(chamado)

    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor")

    # 2) Roteamento pela classificação, já aplicado dentro do chain

    # 3) Fallback IA no chain → já dentro de router_chain

    # 4) Se setor financeiro, override financeiro
    if setor in ("Faturamento", "Financeiro / Tributos"):
        ov = override_finance(text)
        if ov:
            setor = ov

    # 5) Se for coleção de autorização, override de autorização
    coll = collection_for(setor, chamado.classificacao)
    if coll == settings.QDRANT_COLLECTION_AUT:
        ov = override_autorizacao(text)
        if ov:
            setor = ov

    # 6) Busca vetorial no Qdrant e retorno do payload
    result = selector.select(setor, chamado)
    return Resposta(**result)

@app.post("/debug-classify/", response_model=RespostaDebug, dependencies=[Depends(get_api_key)])
async def debug_classify(chamado: Chamado):
    text = f"{chamado.titulo} {chamado.descricao}".lower()

    # Mesma cadeia de roteamento
    setor = router_chain.handle(chamado)
    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor")

    # Mesmos overrides de pós-roteamento
    if setor in ("Faturamento", "Financeiro / Tributos"):
        ov = override_finance(text)
        if ov:
            setor = ov

    coll = collection_for(setor, chamado.classificacao)
    if coll == settings.QDRANT_COLLECTION_AUT:
        ov = override_autorizacao(text)
        if ov:
            setor = ov

    
    raw_model_response = {}

    # Busca vetor e payload
    result = selector.select(setor, chamado)
    return RespostaDebug(**result, raw_model_response=raw_model_response)

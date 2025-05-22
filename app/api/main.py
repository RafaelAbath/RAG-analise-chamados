import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader

from core.config import settings
from core.models import Chamado, Resposta, RespostaDebug
from core.sector_meta import sector_info, allowed_sectors
from routing import router_chain
from services.tech_selector import TechSelector
from services.logger import logger

app = FastAPI(title="API de RAG para Chamados")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)


def get_api_key(key: str = Depends(api_key_header)):
    if key != settings.API_KEY:
        raise HTTPException(401, "Chave de API inválida ou ausente")
    return key

selector = TechSelector()

@app.post("/classify/", response_model=Resposta, dependencies=[Depends(get_api_key)])
async def classify_and_assign(chamado: Chamado):
    setor = router_chain.handle(chamado)
    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor do chamado")
    info = sector_info.get(setor)
    if not info:
        raise HTTPException(500, f"Sem metadados para setor '{setor}'")

    result = selector.select(setor, chamado, info)
    return Resposta(**result)

@app.post("/debug-classify/", response_model=RespostaDebug, dependencies=[Depends(get_api_key)])
async def debug_classify(chamado: Chamado):
    # mesma lógica porém inclui raw_model_response
    setor = router_chain.handle(chamado)
    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor do chamado")
    info = sector_info.get(setor)
    if not info:
        raise HTTPException(500, f"Sem metadados para setor '{setor}'")

    debug = selector.select(setor, chamado, info)
    # acrescentar raw_model_response se necessário
    return RespostaDebug(**debug, raw_model_response={})

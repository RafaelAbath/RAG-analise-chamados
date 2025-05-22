import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from routing import router_chain, llm_router
from routing.utils import clean_setor

from routing.keywords       import KeywordRouter
from routing.classification import ClassificationRouter
from core.config import settings
from core.models import Chamado, Resposta, RespostaDebug
from routing import router_chain
from routing.finance import override_finance
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
kw_router   = KeywordRouter()
cls_router  = ClassificationRouter()

@app.post("/classify/", response_model=Resposta, dependencies=[Depends(get_api_key)])
async def classify_and_assign(chamado: Chamado):
    text = f"{chamado.protocolo} {chamado.descricao}".lower()

    # 1) KEYWORD -------------------------------------------------------------
    setor = kw_router.handle(chamado)
    proveniencia = None
    if setor:
        proveniencia = "keyword"
    # 2) CLASSIFY ------------------------------------------------------------
    if not setor:
        setor = cls_router.handle(chamado)
        if setor:
            proveniencia = "classify"
    # 3) LLM + QDRANT --------------------------------------------------------
    if not setor:
        setor = llm_router.handle(chamado)
        proveniencia = "llm"
    # 4) FINANCE OVERRIDE ----------------------------------------------------
    if setor in ("Faturamento", "Financeiro / Tributos"):
        ov = override_finance(text)
        if ov:
            setor, proveniencia = ov, "finance"

    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor")

    result = selector.select(setor, chamado)
    return Resposta(**result, proveniencia=proveniencia)

@app.post("/debug-classify/", response_model=RespostaDebug, dependencies=[Depends(get_api_key)])
async def debug_classify(chamado: Chamado):
    text = f"{chamado.protocolo} {chamado.descricao}".lower()

    # 1) pré-roteamento por keywords e classificação (igual ao classify)
    setor = router_chain.handle(chamado)
    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor")
    if setor in ("Faturamento", "Financeiro / Tributos"):
        ov = override_finance(text)
        if ov:
            setor = ov

    # 2) chame a LLM **diretamente** para ver o que sai
    system_msg = (
        "Você é um roteador de chamados. Responda APENAS com um dos setores válidos:\n"
        + ", ".join(llm_router.allowed_sectors)
    )
    user_msg = f"Título: {chamado.protocolo}\nDescrição: {chamado.descricao}"
    raw = llm_router.llm.chat.completions.create(
        model=settings.FINETUNED_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg}
        ],
        temperature=0.0
    )
    bruto = clean_setor(raw.choices[0].message.content.strip())

    # 3) decide a collection e busca o técnico
    result = selector.select(bruto, chamado)

    # 4) devolva tudo no debug
    return RespostaDebug(
        setor_ia        = result["setor_ia"],
        tecnico_id      = result["tecnico_id"],
        tecnico_nome    = result["tecnico_nome"],
        tecnico_setor   = result["tecnico_setor"],
        responsabilidades = result["responsabilidades"],
        exemplos        = result["exemplos"],
        confianca       = result["confianca"],
        raw_model_response = {
            "llm_raw": raw.choices[0].message.content.strip(),
            "llm_setor": bruto
        }
    )
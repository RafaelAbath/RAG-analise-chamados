import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader

from core.config import settings
from core.models import Chamado, Resposta, RespostaDebug
from routing import router_chain, llm_router
from routing.utils import clean_setor
from routing.finance import override_finance
from services.tech_selector import TechSelector

# -----------------------------------------------------------------------------
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
    # 1️⃣ Roteamento completo
    setor = router_chain.handle(chamado)

    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor")

    # 2️⃣ Ajuste fino para casos financeiros
    texto = f"{chamado.protocolo} {chamado.descricao}".lower()

    # 1️⃣ Pipeline completo
    setor = router_chain.handle(chamado)
    if not setor:
        raise HTTPException(400, "Não foi possível determinar o setor")

    # 2️⃣ Override financeiro **somente** se a collection for 'financeiros'
    if chamado.collection == settings.QDRANT_COLL_FIN:
        setor, prov_fin = override_finance(setor, texto)
        if prov_fin:
            chamado.proveniencia = prov_fin      # marca 'finance_override'
    # caso contrário, não faz nada

    # 3️⃣ Selecionar técnico
    result = selector.select(setor, chamado)
    return Resposta(
        **result,
        proveniencia=getattr(chamado, "proveniencia", "desconhecido"),
    )
@app.post("/debug-classify/", response_model=RespostaDebug, dependencies=[Depends(get_api_key)])
async def debug_classify(chamado: Chamado):
    """
    Faz apenas o segundo passe LLM (LLMSecondPassRouter) e devolve
    tanto a resposta crua quanto o técnico selecionado — útil para testar o modelo.
    """
    # 1️⃣ Chamada direta ao LLMSecondPassRouter
    system_msg = (
        "Você é um roteador de chamados. Responda APENAS com um dos setores válidos:\n"
        + ", ".join(llm_router.allowed)                     # lista de setores permitidos
    )
    user_msg = f"Protocolo: {chamado.protocolo}\nDescrição: {chamado.descricao}"

    raw = llm_router.llm.chat.completions.create(
        model=settings.FINETUNED_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
    )

    setor_bruto = clean_setor(raw.choices[0].message.content.strip())

    if not setor_bruto:
        raise HTTPException(400, "LLM não retornou um setor válido")

    # 2️⃣ Selecionar técnico com base na saída bruta do LLM
    result = selector.select(setor_bruto, chamado)

    # 3️⃣ Resposta de depuração
    return RespostaDebug(
        setor_ia=result["setor_ia"],
        tecnico_id=result["tecnico_id"],
        tecnico_nome=result["tecnico_nome"],
        tecnico_setor=result["tecnico_setor"],
        responsabilidades=result["responsabilidades"],
        exemplos=result["exemplos"],
        confianca=result["confianca"],
        raw_model_response={
            "llm_raw": raw.choices[0].message.content.strip(),
            "llm_setor": setor_bruto,
        },
    )

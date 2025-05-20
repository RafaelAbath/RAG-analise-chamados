import os, logging
from typing import Any, Dict
from difflib import get_close_matches

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from router_rules import route_by_keywords, override_finance   # suas regras

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ───── variáveis de ambiente ────────────────────────────────────────────
COLLECTION_NIP  = os.getenv("QDRANT_COLLECTION_NIP", "nip_reclames")
COLLECTION      = os.getenv("QDRANT_COLLECTION",     "tecnicos")
COLL_AUT        = os.getenv("QDRANT_COLLECTION_AUT",  "autorizacao_geral")

OPENAI_KEY      = os.getenv("OPENAI_API_KEY")
FINETUNED_MODEL = os.getenv("FINETUNED_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
QDRANT_URL      = os.getenv("QDRANT_URL")
QDRANT_API_KEY  = os.getenv("QDRANT_API_KEY")
API_KEY         = os.getenv("API_KEY")

SUB_AUT = [
    "Autorização",
    "Medicamento",
    "OPME",
    "Garantia de Atendimento (Busca de rede)",
]

# ───── autenticação simples por header ──────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)
def get_api_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(401, "Chave de API inválida ou ausente")
    return key

# ───── metadados dos setores ────────────────────────────────────────────
df_meta = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
required = {"Setor", "Responsabilidades", "Exemplos"}
missing  = required - set(df_meta.columns)
if missing:
    raise RuntimeError(f"Colunas faltando no CSV: {missing}")

_sector_info: Dict[str, Dict[str, str]] = {
    row["Setor"]: {
        "responsabilidades": str(row["Responsabilidades"]).strip(),
        "exemplos":          str(row["Exemplos"]).strip(),
    }
    for _, row in df_meta.iterrows()
}
ALLOWED_SECTORS = list(_sector_info.keys())

# ───── clientes ─────────────────────────────────────────────────────────
openai  = OpenAI(api_key=OPENAI_KEY)
qdrant  = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
app     = FastAPI(title="API de RAG para Chamados")

# ───── modelos ──────────────────────────────────────────────────────────
class Chamado(BaseModel):
    titulo: str
    descricao: str
    classificacao: str | None = None          # novo campo opcional

class Resposta(BaseModel):
    setor_ia: str
    tecnico_id: int
    tecnico_nome: str
    tecnico_setor: str
    confianca: float

class RespostaDebug(Resposta):
    raw_model_response: Dict[str, Any]

# ───── helpers ──────────────────────────────────────────────────────────
def clean_setor(txt: str) -> str:
    return txt.split(":", 1)[1].strip() if ":" in txt else txt.strip()

def collection_for(setor: str, classificacao: str | None) -> str:
    if setor == "Autorização":
        return COLL_AUT                              # sempre dentro de autorização_geral
    if classificacao and classificacao.lower() == "autorizacao_geral":
        return COLL_AUT                              # front forçou
    gatilhos = ("nip", "reclame", "ans", "judicial")
    return COLLECTION_NIP if any(k in setor.lower() for k in gatilhos) else COLLECTION

def refine_autorizacao(setor: str, texto_lower: str, classificacao: str | None) -> str:
    if setor != "Autorização":
        return setor
    # prioridade 1: campo classificacao vindo do front
    if classificacao and classificacao in SUB_AUT:
        return classificacao
    # prioridade 2: palavras-chave
    if "opme" in texto_lower:
        return "OPME"
    if "medic" in texto_lower:
        return "Medicamento"
    if "busca de rede" in texto_lower or "garantia de atendimento" in texto_lower:
        return "Garantia de Atendimento (Busca de rede)"
    return setor   # permanece genérico

# ───── endpoint main ────────────────────────────────────────────────────
@app.post("/classify/", response_model=Resposta, dependencies=[Depends(get_api_key)])
async def classify_and_assign(chamado: Chamado):
    full_lower = (chamado.titulo + " " + chamado.descricao).lower()

    # 1. pré-roteamento por palavras-chave (NIP, OPME, HC…)
    setor_ia = route_by_keywords(full_lower)

    # 2. LLM se necessário
    if not setor_ia:
        system_msg = (
            "Você é um roteador de chamados. Responda APENAS com um dos setores válidos:\n"
            + ", ".join(ALLOWED_SECTORS)
        )
        user_msg = f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}"
        resp = openai.chat.completions.create(
            model=FINETUNED_MODEL,
            messages=[{"role": "system", "content": system_msg},
                      {"role": "user",   "content": user_msg}],
            temperature=0.0,
        )
        bruto = clean_setor(resp.choices[0].message.content.strip())
        if bruto not in _sector_info:
            match = get_close_matches(bruto, ALLOWED_SECTORS, n=1, cutoff=0.6)
            if not match:
                raise HTTPException(500, f"Setor '{bruto}' não é válido.")
            setor_ia = match[0]
        else:
            setor_ia = bruto

    # 3. ajuste financeiro
    if setor_ia in ("Faturamento", "Financeiro / Tributos"):
        alt = override_finance(full_lower)
        if alt:
            setor_ia = alt

    # 4. refino dentro de Autorização
    setor_ia = refine_autorizacao(setor_ia, full_lower, chamado.classificacao)

    # 5. embedding + busca
    info = _sector_info.get(setor_ia)
    if not info:
        raise HTTPException(500, f"Sem metadados para setor '{setor_ia}'.")
    text_search = (
        f"Responsabilidades: {info['responsabilidades']}. "
        f"Exemplos: {info['exemplos']}. "
        f"Chamado: {chamado.titulo}. {chamado.descricao}"
    )
    emb = openai.embeddings.create(model=EMBEDDING_MODEL, input=text_search).data[0].embedding

    coll = collection_for(setor_ia, chamado.classificacao)
    hits = qdrant.search(
        collection_name=coll,
        query_vector=emb,
        limit=1,
        with_payload=True,
        query_filter=Filter(must=[FieldCondition(key="setor", match=MatchValue(value=setor_ia))]),
    )
    if not hits:
        raise HTTPException(404, f"Nenhum técnico encontrado para o setor {setor_ia}.")

    hit = hits[0]
    payload = hit.payload
    if payload["setor"].lower() != setor_ia.lower():
        logging.warning(f"Setor IA '{setor_ia}' ≠ payload '{payload['setor']}'")

    return Resposta(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score,
    )

# ───── endpoint debug ───────────────────────────────────────────────────
@app.post("/debug-classify/", response_model=RespostaDebug, dependencies=[Depends(get_api_key)])
async def debug_classify(chamado: Chamado):
    # reaproveita lógica principal, mas devolve raw_model_response
    resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[{"role": "user",
                   "content": f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}"}],
        temperature=0.0,
    )
    bruto    = clean_setor(resp.choices[0].message.content.strip())
    setor_ia = bruto if bruto in _sector_info else get_close_matches(
        bruto, ALLOWED_SECTORS, n=1, cutoff=0.6)[0]

    setor_ia = refine_autorizacao(setor_ia, (chamado.titulo + " " + chamado.descricao).lower(),
                                  chamado.classificacao)

    info = _sector_info[setor_ia]
    emb = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=(f"Responsabilidades: {info['responsabilidades']}. "
               f"Exemplos: {info['exemplos']}. "
               f"Chamado: {chamado.titulo}. {chamado.descricao}")
    ).data[0].embedding

    coll = collection_for(setor_ia, chamado.classificacao)
    hit  = qdrant.search(
        collection_name=coll,
        query_vector=emb,
        limit=1,
        with_payload=True,
        query_filter=Filter(must=[FieldCondition(key="setor", match=MatchValue(value=setor_ia))]),
    )[0]

    return RespostaDebug(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=hit.payload["nome"],
        tecnico_setor=hit.payload["setor"],
        confianca=hit.score,
        raw_model_response=resp.model_dump(),
    )

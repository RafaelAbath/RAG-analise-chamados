import os
import logging
from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

# ─── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)

# ─── Variáveis de ambiente ─────────────────────────────────────────────
OPENAI_KEY      = os.getenv("OPENAI_API_KEY")
FINETUNED_MODEL = os.getenv("FINETUNED_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
QDRANT_URL      = os.getenv("QDRANT_URL")
QDRANT_API_KEY  = os.getenv("QDRANT_API_KEY")
COLLECTION      = os.getenv("QDRANT_COLLECTION")
API_KEY         = os.getenv("API_KEY")

# ─── Autenticação por API Key ───────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)
def get_api_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(401, "Chave de API inválida ou ausente")
    return key

# ─── Carrega metadados dos setores do CSV ───────────────────────────────
_sector_info: Dict[str, Dict[str, str]] = {}
df_meta = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
required = {"Setor", "Responsabilidades", "Exemplos"}
missing = required - set(df_meta.columns)
if missing:
    raise RuntimeError(f"Colunas faltando no CSV: {missing}")

for _, row in df_meta.iterrows():
    setor = row["Setor"]
    _sector_info[setor] = {
        "responsabilidades": str(row["Responsabilidades"]).strip(),
        "exemplos":           str(row["Exemplos"]).strip()
    }

# ─── Inicializa OpenAI e Qdrant ────────────────────────────────────────
openai = OpenAI(api_key=OPENAI_KEY)
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

app = FastAPI(title="API de RAG para Chamados")

# ─── Schemas Pydantic ───────────────────────────────────────────────────
class Chamado(BaseModel):
    titulo: str
    descricao: str

class Resposta(BaseModel):
    setor_ia: str
    tecnico_id: int
    tecnico_nome: str
    tecnico_setor: str
    confianca: float

class RespostaDebug(Resposta):
    raw_model_response: Dict[str, Any]

# ─── Endpoint /classify/ ────────────────────────────────────────────────
@app.post(
    "/classify/",
    response_model=Resposta,
    dependencies=[Depends(get_api_key)]
)
async def classify_and_assign(chamado: Chamado):
    # 1) Finetuned define setor
    prompt = (
        "Analise o seguinte chamado e diga apenas o setor responsável:\n\n"
        f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}\n"
    )
    model_resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    setor_ia = model_resp.choices[0].message.content.strip()

    # 2) Recupera descrições detalhadas do setor
    info = _sector_info.get(setor_ia)
    if not info:
        raise HTTPException(500, f"Metadados do setor '{setor_ia}' não encontrados.")

    # 3) Embedding combinando responsabilidades, exemplos e texto do chamado
    text_for_search = (
        f"Responsabilidades: {info['responsabilidades']}. "
        f"Exemplos: {info['exemplos']}. "
        f"Chamado: {chamado.titulo}. {chamado.descricao}"
    )
    emb = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_for_search
    ).data[0].embedding

    # 4) Busca vetorial **filtrada** pelo setor
    hits = qdrant.search(
        collection_name=COLLECTION,
        query_vector=emb,
        limit=1,
        with_payload=True,
        filter=Filter(
            must=[FieldCondition(key="setor", match=MatchValue(value=setor_ia))]
        )
    )
    if not hits:
        raise HTTPException(404, f"Nenhum técnico encontrado para o setor {setor_ia}.")

    hit = hits[0]
    payload = hit.payload

    # Log de divergência de setor (opcional)
    if payload["setor"].lower() != setor_ia.lower():
        logging.warning(
            f"Setor IA '{setor_ia}' ≠ payload '{payload['setor']}'"
        )

    # 5) Retorna a resposta final
    return Resposta(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score
    )

# ─── Endpoint /debug-classify/ ─────────────────────────────────────────
@app.post(
    "/debug-classify/",
    response_model=RespostaDebug,
    dependencies=[Depends(get_api_key)]
)
async def debug_classify(chamado: Chamado):
    # Repete a lógica de classify, mas inclui raw_model_response
    prompt = (
        "Analise o seguinte chamado e diga apenas o setor responsável:\n\n"
        f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}\n"
    )
    model_resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    setor_ia = model_resp.choices[0].message.content.strip()

    info = _sector_info.get(setor_ia)
    if not info:
        raise HTTPException(500, f"Metadados do setor '{setor_ia}' não encontrados.")

    emb = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=(
            f"Responsabilidades: {info['responsabilidades']}. "
            f"Exemplos: {info['exemplos']}. "
            f"Chamado: {chamado.titulo}. {chamado.descricao}"
        )
    ).data[0].embedding

    hits = qdrant.search(
        collection_name=COLLECTION,
        query_vector=emb,
        limit=1,
        with_payload=True,
        filter=Filter(
            must=[FieldCondition(key="setor", match=MatchValue(value=setor_ia))]
        )
    )
    if not hits:
        raise HTTPException(404, f"Nenhum técnico encontrado para o setor {setor_ia}.")

    hit = hits[0]
    payload = hit.payload

    if payload["setor"].lower() != setor_ia.lower():
        logging.warning(
            f"Setor IA '{setor_ia}' ≠ payload '{payload['setor']}'"
        )

    return RespostaDebug(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score,
        raw_model_response=model_resp.model_dump()
    )

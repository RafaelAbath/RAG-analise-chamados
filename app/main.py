import os
import logging
from typing import Any, Dict
from difflib import get_close_matches

import pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

logging.basicConfig(level=logging.INFO)

OPENAI_KEY      = os.getenv("OPENAI_API_KEY")
FINETUNED_MODEL = os.getenv("FINETUNED_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
QDRANT_URL      = os.getenv("QDRANT_URL")
QDRANT_API_KEY  = os.getenv("QDRANT_API_KEY")
COLLECTION      = os.getenv("QDRANT_COLLECTION")
API_KEY         = os.getenv("API_KEY")

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)
def get_api_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(401, "Chave de API inválida ou ausente")
    return key

# Carrega metadados dos setores
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

# Lista de setores válidos
ALLOWED_SECTORS = list(_sector_info.keys())

openai = OpenAI(api_key=OPENAI_KEY)
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
app = FastAPI(title="API de RAG para Chamados")

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

def clean_setor(raw: str) -> str:
   
    return raw.split(":", 1)[1].strip() if ":" in raw else raw.strip()

@app.post("/classify/", response_model=Resposta, dependencies=[Depends(get_api_key)])
async def classify_and_assign(chamado: Chamado):
    
    system_msg = (
        "Você é um roteador de chamados. Responda **APENAS** com um dos setores válidos abaixo (sem nenhum outro texto):\n"
        + ", ".join(ALLOWED_SECTORS)
    )
    user_msg = (
        f"Analise este chamado e escolha um setor:\n"
        f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}"
    )
    model_resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg}
        ],
        temperature=0.0
    )

    
    raw_sector   = model_resp.choices[0].message.content.strip()
    setor_bruto  = clean_setor(raw_sector)
    if setor_bruto not in _sector_info:
        
        matches = get_close_matches(setor_bruto, ALLOWED_SECTORS, n=1, cutoff=0.6)
        if not matches:
            raise HTTPException(500, f"Setor '{setor_bruto}' não é válido.")
        setor_ajustado = matches[0]
    else:
        setor_ajustado = setor_bruto

    info = _sector_info[setor_ajustado]
    setor_ia = setor_ajustado

    
    text_for_search = (
        f"Responsabilidades: {info['responsabilidades']}. "
        f"Exemplos: {info['exemplos']}. "
        f"Chamado: {chamado.titulo}. {chamado.descricao}"
    )
    emb = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_for_search
    ).data[0].embedding

    hits = qdrant.search(
        collection_name=COLLECTION,
        query_vector=emb,
        limit=1,
        with_payload=True,
        query_filter=Filter(
            must=[FieldCondition(key="setor", match=MatchValue(value=setor_ia))]
        )
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
        confianca=hit.score
    )

@app.post("/debug-classify/", response_model=RespostaDebug, dependencies=[Depends(get_api_key)])
async def debug_classify(chamado: Chamado):
    prompt = (
        "Analise o seguinte chamado e diga apenas o setor responsável:\n\n"
        f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}\n"
    )
    model_resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    raw_sector = model_resp.choices[0].message.content.strip()
    setor_ia = clean_setor(raw_sector)

    info = _sector_info.get(setor_ia)
    if not info:
        raise HTTPException(500, f"Metadados do setor '{setor_ia}' (original: '{raw_sector}') não encontrados.")

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
        query_filter=Filter(
            must=[FieldCondition(key="setor", match=MatchValue(value=setor_ia))]
        )
    )
    if not hits:
        raise HTTPException(404, f"Nenhum técnico encontrado para o setor {setor_ia}.")

    hit = hits[0]
    payload = hit.payload

    if payload["setor"].lower() != setor_ia.lower():
        logging.warning(f"Setor IA '{setor_ia}' ≠ payload '{payload['setor']}'")

    return RespostaDebug(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score,
        raw_model_response=model_resp.model_dump()
    )

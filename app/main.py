import os
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from openai import OpenAI
from qdrant_client import QdrantClient

# ─── Configuração de logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)

# ─── Carrega variáveis de ambiente ─────────────────────────────────────────────
OPENAI_KEY      = os.getenv("OPENAI_API_KEY")
FINETUNED_MODEL = os.getenv("FINETUNED_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
QDRANT_URL      = os.getenv("QDRANT_URL")
QDRANT_API_KEY  = os.getenv("QDRANT_API_KEY")
COLLECTION      = os.getenv("QDRANT_COLLECTION")
API_KEY         = os.getenv("API_KEY")  # sua chave secreta para autenticação

# ─── Segurança por API Key ──────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

def get_api_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(401, "Chave de API inválida ou ausente")
    return key

# ─── Inicializa clientes OpenAI e Qdrant ────────────────────────────────────────
openai = OpenAI(api_key=OPENAI_KEY)
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

app = FastAPI(title="API de RAG para Chamados")

# ─── Modelos de dados ───────────────────────────────────────────────────────────
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

# ─── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/classify/", response_model=Resposta, dependencies=[Depends(get_api_key)])
async def classify_and_assign(chamado: Chamado):
    # 1) Modelo finetuned define setor
    prompt = (
        "Analise o seguinte chamado e diga apenas o setor responsável:\n\n"
        f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}\n"
    )
    resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    setor_ia = resp.choices[0].message.content.strip()

    # 2) Embedding para busca vetorial
    text_for_search = f"{setor_ia}: {chamado.titulo}. {chamado.descricao}"
    emb_resp = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_for_search
    )
    emb = emb_resp.data[0].embedding

    # 3) Busca no Qdrant
    hits = qdrant.search(
        collection_name=COLLECTION,
        query_vector=emb,
        limit=1,
        with_payload=True,
    )
    if not hits:
        raise HTTPException(404, "Nenhum técnico encontrado para o setor sugerido.")

    hit = hits[0]
    payload = hit.payload

    # 4) Validação simples
    if payload["setor"].lower() != setor_ia.lower():
        logging.warning(
            f"Setor IA '{setor_ia}' difere do payload '{payload['setor']}'"
        )

    return Resposta(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score
    )

@app.post("/debug-classify/", response_model=RespostaDebug, dependencies=[Depends(get_api_key)])
async def debug_classify(chamado: Chamado):
    # Reutiliza a mesma lógica de classify_and_assign, devolvendo raw_model_response
    prompt = (
        "Analise o seguinte chamado e diga apenas o setor responsável:\n\n"
        f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}\n"
    )
    resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    setor_ia = resp.choices[0].message.content.strip()

    text_for_search = f"{setor_ia}: {chamado.titulo}. {chamado.descricao}"
    emb_resp = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_for_search
    )
    emb = emb_resp.data[0].embedding

    hits = qdrant.search(
        collection_name=COLLECTION,
        query_vector=emb,
        limit=1,
        with_payload=True,
    )
    if not hits:
        raise HTTPException(404, "Nenhum técnico encontrado para o setor sugerido.")

    hit = hits[0]
    payload = hit.payload

    if payload["setor"].lower() != setor_ia.lower():
        logging.warning(
            f"Setor IA '{setor_ia}' difere do payload '{payload['setor']}'"
        )

    return RespostaDebug(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score,
        raw_model_response=resp.model_dump()
    )

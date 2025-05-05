import os, logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from qdrant_client import QdrantClient

# Habilita logging
logging.basicConfig(level=logging.INFO)

# Configurações de ambiente
OPENAI_KEY      = os.getenv("OPENAI_API_KEY")
FINETUNED_MODEL = os.getenv("FINETUNED_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
QDRANT_URL      = os.getenv("QDRANT_URL")
QDRANT_API_KEY  = os.getenv("QDRANT_API_KEY")
COLLECTION      = os.getenv("QDRANT_COLLECTION")

# Inicializa clientes
openai = OpenAI(api_key=OPENAI_KEY)
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
app    = FastAPI(title="API de RAG para Chamados")

# Modelos Pydantic
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

@app.post("/classify/", response_model=Resposta)
async def classify_and_assign(chamado: Chamado):
    # 1) IA finetuned define setor
    prompt = (
        f"Analise o seguinte chamado e diga apenas o setor responsável:\n\n"
        f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}\n"
    )
    resp = openai.chat.completions.create(
        model=FINETUNED_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    setor_ia = resp.choices[0].message.content.strip()

    # 2) Preparar texto para embedding
    text_for_search = f"{setor_ia}: {chamado.titulo}. {chamado.descricao}"
    emb_resp = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_for_search
    )
    emb = emb_resp.data[0].embedding

    # 3) Busca no Qdrant pelo vetor mais próximo
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

    # Validação simples de consistência (opcional)
    if payload["setor"].lower() != setor_ia.lower():
        logging.warning(f"Setor gerado pela IA '{setor_ia}' difere do payload '{payload['setor']}'")

    return Resposta(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score
    )

@app.post("/debug-classify/", response_model=RespostaDebug)
async def debug_classify(chamado: Chamado):
    # Mesma lógica de classify, mas retorna raw_model_response
    prompt = (
        f"Analise o seguinte chamado e diga apenas o setor responsável:\n\n"
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
        logging.warning(f"Setor IA '{setor_ia}' difere do payload '{payload['setor']}'")

    # Retorna também o raw response
    return RespostaDebug(
        setor_ia=setor_ia,
        tecnico_id=hit.id,
        tecnico_nome=payload["nome"],
        tecnico_setor=payload["setor"],
        confianca=hit.score,
        raw_model_response=resp.model_dump()
    )

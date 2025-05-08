import os
import pandas as pd
from collections import namedtuple

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PayloadSchema,
    PayloadSchemaType,
)

from openai import OpenAI

Point = namedtuple("Point", ["id", "vector", "payload"])

# ─── Variáveis de ambiente ─────────────────────────────────────────────
QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION     = os.getenv("QDRANT_COLLECTION")
EMBED_MODEL    = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY     = os.getenv("OPENAI_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
openai = OpenAI(api_key=OPENAI_KEY)

# ─── (Re)cria a coleção com índice em `setor` ──────────────────────────
if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION, wait=True)

client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    payload_schema={"setor": PayloadSchema(type=PayloadSchemaType.KEYWORD)},
    wait=True,
)

# ─── Lê CSV e valida colunas ───────────────────────────────────────────
df = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
required = {"Setor", "Técnico Responsável", "Responsabilidades", "Exemplos"}
missing = required - set(df.columns)
if missing:
    raise RuntimeError(f"Colunas faltando no CSV: {missing}")

# ─── Gera embeddings e monta pontos ────────────────────────────────────
points = []
for idx, row in df.iterrows():
    text = (
        f"Responsabilidades: {row['Responsabilidades']}. "
        f"Exemplos: {row['Exemplos']}"
    )
    emb = openai.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding

    payload = {
        "nome":              row["Técnico Responsável"],
        "setor":             row["Setor"],
        "responsabilidades": row["Responsabilidades"],
        "exemplos":          row["Exemplos"],
    }

    points.append(Point(id=idx, vector=emb, payload=payload))

# ─── Faz upload para o Qdrant Cloud ────────────────────────────────────
client.upload_points(collection_name=COLLECTION, points=points, wait=True)

print(f"Indexados {len(points)} técnicos em '{COLLECTION}'.")

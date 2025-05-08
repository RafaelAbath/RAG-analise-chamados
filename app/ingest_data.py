import os
import pandas as pd
from collections import namedtuple

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType
from openai import OpenAI

Point = namedtuple("Point", ["id", "vector", "payload"])

QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION     = os.getenv("QDRANT_COLLECTION")
EMBED_MODEL    = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY     = os.getenv("OPENAI_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
openai = OpenAI(api_key=OPENAI_KEY)

# 1) Apaga coleção antiga, se existir
if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION)

# 2) Cria nova coleção apenas com vetor
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# 3) Garante índice keyword no payload "setor"
client.create_payload_index(
    collection_name=COLLECTION,
    field_name="setor",
    field_schema=PayloadSchemaType.KEYWORD,
)

# 4) Lê e valida CSV
df = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
required = {"Setor", "Técnico Responsável", "Responsabilidades", "Exemplos"}
missing = required - set(df.columns)
if missing:
    raise RuntimeError(f"Colunas faltando no CSV: {missing}")

# 5) Constrói pontos
points = []
for idx, row in df.iterrows():
    text = (
        f"Responsabilidades: {row['Responsabilidades']}. "
        f"Exemplos: {row['Exemplos']}"
    )
    emb = openai.embeddings.create(
        model=EMBED_MODEL,
        input=text
    ).data[0].embedding

    payload = {
        "nome":              row["Técnico Responsável"],
        "setor":             row["Setor"],
        "responsabilidades": row["Responsabilidades"],
        "exemplos":          row["Exemplos"],
    }

    points.append(Point(id=int(idx), vector=emb, payload=payload))

# 6) Envia para o Qdrant em lotes
client.upload_points(
    collection_name=COLLECTION,
    points=points,
    batch_size=500,
)

print(f"Indexados {len(points)} técnicos em '{COLLECTION}'.")

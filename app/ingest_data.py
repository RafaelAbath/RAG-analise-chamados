import os
import pandas as pd
from collections import namedtuple

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchema, PayloadSchemaType
from openai import OpenAI

Point = namedtuple("Point", ["id", "vector", "payload"])

QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION     = os.getenv("QDRANT_COLLECTION")
EMBED_MODEL    = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY     = os.getenv("OPENAI_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
openai = OpenAI(api_key=OPENAI_KEY)

if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION)

client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    payload_schema={
        "setor": PayloadSchema(type=PayloadSchemaType.KEYWORD)
    }
)

df = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
required_cols = {"Setor", "Técnico Responsável", "Responsabilidades", "Exemplos"}
missing = required_cols - set(df.columns)
if missing:
    raise RuntimeError(f"Colunas faltando no CSV: {missing}")

points = []
for idx, row in df.iterrows():
    text_to_embed = (
        f"Responsabilidades: {row['Responsabilidades']}. "
        f"Exemplos: {row['Exemplos']}"
    )
    emb_resp = openai.embeddings.create(model=EMBED_MODEL, input=text_to_embed)
    emb = emb_resp.data[0].embedding

    payload = {
        "nome":              row["Técnico Responsável"],
        "setor":             row["Setor"],
        "responsabilidades": row["Responsabilidades"],
        "exemplos":          row["Exemplos"],
    }

    points.append(Point(id=idx, vector=emb, payload=payload))

client.upload_points(collection_name=COLLECTION, points=points)

print(f"Indexados {len(points)} técnicos em '{COLLECTION}'.")

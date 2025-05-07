import os
import pandas as pd
from collections import namedtuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from openai import OpenAI

# Define Point com atributos .id, .vector, .payload
Point = namedtuple("Point", ["id", "vector", "payload"])

# Variáveis de ambiente (Qdrant Cloud + OpenAI)
QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION     = os.getenv("QDRANT_COLLECTION")
EMBED_MODEL    = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY     = os.getenv("OPENAI_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
openai = OpenAI(api_key=OPENAI_KEY)

# (Re)cria coleção no Qdrant
if client.collection_exists(collection_name=COLLECTION):
    client.delete_collection(collection_name=COLLECTION)
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Carrega o novo CSV com as quatro colunas
df = pd.read_csv("data/tecnicos_secoes.csv")  # colunas: Setor, Técnico Responsável, Responsabilidades, Exemplos

points = []
for idx, row in df.iterrows():
    # Agrupa responsabilidades + exemplos numa string para o embedding
    text_to_embed = (
        f"Responsabilidades: {row['Responsabilidades']}. "
        f"Exemplos: {row['Exemplos']}"
    )
    resp = openai.embeddings.create(model=EMBED_MODEL, input=text_to_embed)
    emb = resp.data[0].embedding

    points.append(
        Point(
            id=idx,
            vector=emb,
            payload={
                "nome": row["Técnico Responsável"],
                "setor": row["Setor"],
                "responsabilidades": row["Responsabilidades"],
                "exemplos": row["Exemplos"],
            }
        )
    )

client.upload_records(collection_name=COLLECTION, records=points)
print(f"Indexados {len(points)} técnicos em '{COLLECTION}'.")

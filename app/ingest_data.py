import os
import pandas as pd
from collections import namedtuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from openai import OpenAI

# Define um tipo simples com atributos .id, .vector, .payload
Point = namedtuple("Point", ["id", "vector", "payload"])

# Carrega variáveis de ambiente
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT"))
COLLECTION = os.getenv("QDRANT_COLLECTION")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY  = os.getenv("OPENAI_API_KEY")

# Inicializa clientes
client = QdrantClient(url=f"http://{QDRANT_HOST}:{QDRANT_PORT}")
openai = OpenAI(api_key=OPENAI_KEY)

# (Re)cria coleção sem usar recreate_collection
if client.collection_exists(collection_name=COLLECTION):
    client.delete_collection(collection_name=COLLECTION)
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Carrega CSV – colunas: Setor, Técnico Responsável, Atribuições
df = pd.read_csv("data/tecnicos_secoes.csv")  # ou o nome correto do seu CSV

points = []
for idx, row in df.iterrows():
    # 1) Gera embedding
    resp = openai.embeddings.create(
        model=EMBED_MODEL,
        input=row["Atribuições"]
    )
    emb = resp.data[0].embedding

    # 2) Empacota em Point, que tem .id, .vector, .payload
    points.append(
        Point(
            id=int(idx),
            vector=emb,
            payload={
                "nome": row["Técnico Responsável"],
                "setor": row["Setor"]
            }
        )
    )

# 3) Faz o upload usando upload_records (ou upload_points)
client.upload_records(collection_name=COLLECTION, records=points)
print(f"Indexados {len(points)} técnicos em '{COLLECTION}'.")

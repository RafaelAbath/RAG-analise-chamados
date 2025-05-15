import os
import pandas as pd
from collections import namedtuple

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType
from openai import OpenAI


Point = namedtuple("Point", ["id", "vector", "payload"])

QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLL_DEFAULT   = os.getenv("QDRANT_COLLECTION",     "tecnicos")
COLL_NIP       = os.getenv("QDRANT_COLLECTION_NIP", "nip_reclames")

EMBED_MODEL    = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY     = os.getenv("OPENAI_API_KEY")
NIP_KEYS       = ("nip", "reclame")      

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
openai  = OpenAI(api_key=OPENAI_KEY)


def choose_collection(setor: str) -> str:
    """Devolve a coleção apropriada pelo nome do setor."""
    return COLL_NIP if any(k in setor.lower() for k in NIP_KEYS) else COLL_DEFAULT

def recreate_collection(name: str):
    """(Re)cria a coleção do zero, já indexando o campo 'setor'."""
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    client.create_payload_index(
        collection_name=name,
        field_name="setor",
        field_schema=PayloadSchemaType.KEYWORD,
    )


for coll in (COLL_DEFAULT, COLL_NIP):
    recreate_collection(coll)


df = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
required = {"Setor", "Técnico Responsável", "Responsabilidades", "Exemplos"}
if missing := (required - set(df.columns)):
    raise RuntimeError(f"Colunas faltando no CSV: {missing}")


buffers = {COLL_DEFAULT: [], COLL_NIP: []}

for idx, row in df.iterrows():
    texto = (
        f"Responsabilidades: {row['Responsabilidades']}. "
        f"Exemplos: {row['Exemplos']}"
    )
    vector = openai.embeddings.create(
        model=EMBED_MODEL,
        input=texto
    ).data[0].embedding

    payload = {
        "nome":              row["Técnico Responsável"],
        "setor":             row["Setor"],
        "responsabilidades": row["Responsabilidades"],
        "exemplos":          row["Exemplos"],
    }

    coll = choose_collection(row["Setor"])
    buffers[coll].append(Point(id=int(idx), vector=vector, payload=payload))


for coll, pts in buffers.items():
    if pts:
        client.upload_points(coll, pts, batch_size=500)
        print(f"Indexados {len(pts)} pontos em '{coll}'.")

print(" Ingestão concluída.")

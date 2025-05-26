import os, sys,pandas as pd, itertools, uuid, json, tqdm
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType
from collections import namedtuple
from services.collection_mapper import collection_for

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
Point = namedtuple("Point", ["id", "vector", "payload"])

settings = __import__("core.config").config.settings     
client   = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
openai   = OpenAI(api_key=settings.OPENAI_API_KEY)

def recreate(coll: str):
    if client.collection_exists(coll):
        client.delete_collection(coll)
    client.create_collection(
        collection_name=coll,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    client.create_payload_index(
        collection_name=coll,
        field_name="setor",
        field_schema=PayloadSchemaType.KEYWORD,
    )

df   = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
miss = {"Setor", "Técnico Responsável", "Responsabilidades", "Exemplos"} - set(df.columns)
if miss:
    raise RuntimeError(f"CSV sem colunas: {miss}")

buffers: dict[str, list[Point]] = {}
for idx, row in tqdm.tqdm(df.iterrows(), total=len(df)):
    setor = row["Setor"].strip()
    coll  = collection_for(setor)
    vec   = openai.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=f"{row['Responsabilidades']} {row['Exemplos']}"
    ).data[0].embedding
    payload = {
        "nome"  : row["Técnico Responsável"],
        "setor" : setor,
        "responsabilidades": row["Responsabilidades"],
        "exemplos": row["Exemplos"],
    }
    buffers.setdefault(coll, []).append(Point(id=int(idx), vector=vec, payload=payload))

for coll, points in buffers.items():
    recreate(coll)
    client.upload_points(coll, points, batch_size=256)
    print(f" {len(points)} pontos → {coll}")
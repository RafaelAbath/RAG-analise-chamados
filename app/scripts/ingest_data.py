import os
import pandas as pd
from collections import namedtuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType
from openai import OpenAI


Point = namedtuple("Point", ["id", "vector", "payload"])


QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_KEY     = os.getenv("QDRANT_API_KEY")
COLL_DEFAULT   = os.getenv("QDRANT_COLLECTION", "tecnicos")
COLL_NIP       = os.getenv("QDRANT_COLLECTION_NIP", "nip_reclames")
COLL_AUT       = os.getenv("QDRANT_COLLECTION_AUT", "autorizacao_geral")

EMBED_MODEL    = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY     = os.getenv("OPENAI_API_KEY")


client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
openai = OpenAI(api_key=OPENAI_KEY)


NIP_KEYS = ("nip", "reclame", "ans", "judicial")

AUT_SETS = {
    "Autorização",
    "Medicamento",
    "Garantia de Atendimento (Busca de rede)",
}

def choose_collection(setor: str) -> str:

    s = setor.strip().lower()
    if setor in AUT_SETS:
        return COLL_AUT
    if any(key in s for key in NIP_KEYS):
        return COLL_NIP
    return COLL_DEFAULT


def recreate(collection_name: str):

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    client.create_payload_index(
        collection_name=collection_name,
        field_name="setor",
        field_schema=PayloadSchemaType.KEYWORD,
    )



for coll in (COLL_DEFAULT, COLL_NIP, COLL_AUT):
    recreate(coll)


csv_path = "data/tecnicos_secoes.csv"
df = pd.read_csv(csv_path, encoding="utf-8-sig")
required_columns = {"Setor", "Técnico Responsável", "Responsabilidades", "Exemplos"}
missing = required_columns - set(df.columns)
if missing:
    raise RuntimeError(f"CSV sem colunas obrigatórias: {missing}")


buffers = {COLL_DEFAULT: [], COLL_NIP: [], COLL_AUT: []}


for idx, row in df.iterrows():
    text = f"Responsabilidades: {row['Responsabilidades']}. Exemplos: {row['Exemplos']}"
    vec = openai.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding

    payload = {
        "nome": row["Técnico Responsável"].strip(),
        "setor": row["Setor"].strip(),
        "responsabilidades": str(row["Responsabilidades"]).strip(),
        "exemplos": str(row["Exemplos"]).strip(),
    }

    coll = choose_collection(row["Setor"])
    buffers[coll].append(Point(id=int(idx), vector=vec, payload=payload))


for coll, points in buffers.items():
    if not points:
        continue
    client.upload_points(collection_name=coll, points=points, batch_size=256)
    print(f"✔  {len(points)} pontos → {coll}")

print(" Ingestão concluída.")

import os, pandas as pd
from collections import namedtuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType
from openai import OpenAI

Point = namedtuple("Point", ["id", "vector", "payload"])

# ── Variáveis de ambiente ─────────────────────────────────────────────
QDRANT_URL  = os.getenv("QDRANT_URL")
QDRANT_KEY  = os.getenv("QDRANT_API_KEY")
COLL_DEFAULT = os.getenv("QDRANT_COLLECTION",        "tecnicos")
COLL_NIP     = os.getenv("QDRANT_COLLECTION_NIP",    "nip_reclames")
COLL_AUT     = os.getenv("QDRANT_COLLECTION_AUT",    "autorizacao_geral")

EMBED_MODEL  = os.getenv("EMBEDDING_MODEL")
OPENAI_KEY   = os.getenv("OPENAI_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
openai  = OpenAI(api_key=OPENAI_KEY)

# grupo de setores → coleção
NIP_KEYS = ("nip", "reclame")
AUT_SETS = {
    "Autorização",
    "Medicamento",
    "OPME",
    "Garantia de Atendimento (Busca de rede)",
}

def choose_collection(setor: str) -> str:
    s = setor.lower()
    if any(k in s for k in NIP_KEYS):
        return COLL_NIP
    if setor in AUT_SETS:
        return COLL_AUT
    return COLL_DEFAULT

def recreate(name):
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

for coll in (COLL_DEFAULT, COLL_NIP, COLL_AUT):
    recreate(coll)

df = pd.read_csv("data/tecnicos_secoes.csv", encoding="utf-8-sig")
req = {"Setor", "Técnico Responsável", "Responsabilidades", "Exemplos"}
if miss := (req - set(df.columns)):
    raise RuntimeError(f"CSV sem colunas: {miss}")

buffers = {c: [] for c in (COLL_DEFAULT, COLL_NIP, COLL_AUT)}

for idx, row in df.iterrows():
    vector = openai.embeddings.create(
        model=EMBED_MODEL,
        input=f"Responsabilidades: {row['Responsabilidades']}. Exemplos: {row['Exemplos']}"
    ).data[0].embedding

    payload = {
        "nome":  row["Técnico Responsável"],
        "setor": row["Setor"],
        "responsabilidades": row["Responsabilidades"],
        "exemplos": row["Exemplos"],
    }
    buffers[choose_collection(row["Setor"])].append(Point(id=int(idx), vector=vector, payload=payload))

for coll, pts in buffers.items():
    if pts:
        client.upload_points(coll, pts, batch_size=256)
        print(f"✔  {len(pts)} pontos → {coll}")

print("✅  Ingestão concluída.")

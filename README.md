# True Auditoria – RAG de Chamados

Uma API de Retrieval-Augmented Generation para classificação e roteamento automático de chamados, usando:

- **OpenAI finetuned** (ChatCompletion)  
- **Qdrant** para busca vetorial  
- **FastAPI**  
- **Docker & Docker Compose**

---

## 📁 Estrutura do Projeto

├── data/
│ └── tecnicos_secoes.csv # Dados dos técnicos e áreas
├── app/
│ ├── ingest_data.py # Indexação em Qdrant
│ ├── main.py # API FastAPI
│ └── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env # Configurações de ambiente

YAML

---

## 🚀 Começando

### 1. Pré-requisitos

- Docker & Docker Compose  
- Conta e chave da OpenAI com acesso ao seu modelo finetuned  

### 2. Configuração

Crie um arquivo `.env` na raiz com:

```dotenv
OPENAI_API_KEY=sk-...
FINETUNED_MODEL=ft-...
EMBEDDING_MODEL=text-embedding-ada-002
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=tecnicos


 Build & Deploy
bash
docker compose up --build -d
indexar documento
docker compose exec api python ingest_data.py

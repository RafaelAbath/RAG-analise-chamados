# True Auditoria – RAG de Chamados

Retrieval-Augmented Generation que **classifica e roteia** chamados internos para o técnico correto.  
Baseada em **FastAPI + OpenAI + Qdrant** e empacotada em Docker.

---

## Novidades (v1.1)

* **Separação de camadas**: `app/`, `scripts/`, `data/`, etc.
* **Configuração centralizada** com `app/core/config.py`.
* **Roteamento modular** usando o padrão Chain of Responsibility em `routing/`.
* **Serviços desacoplados** em `services/`.

---

## Estrutura do Projeto

```
.
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
├── .env.example
├── scripts/
│   └── ingest_data.py
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── models.py
│   │   └── text_utils.py
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── keywords.py
│   │   ├── finance.py
│   │   ├── llm.py
│   │   └── patterns.yml
│   └── services/
│       ├── tech_selector.py
│       └── logger.py
└── data/
    └── tecnicos_secoes.csv
```

---

## Variáveis de Ambiente (`.env`)

```dotenv
# OpenAI
OPENAI_API_KEY=
FINETUNED_MODEL=
EMBEDDING_MODEL=

# Qdrant
QDRANT_URL=
QDRANT_API_KEY=
QDRANT_COLLECTION=
QDRANT_COLLECTION_NIP=
QDRANT_COLLECTION_AUT=

# API
API_KEY=
```

---

## Execução rápida (Docker Compose)

```bash
git clone https://github.com/<user>/true-auditoria-rag.git
cd true-auditoria-rag
cp .env.example .env  # preencha as variáveis

docker compose up --build -d

# Ingestão inicial de dados
docker compose exec api python scripts/ingest_data.py
```

---

## Endpoints

| Método | Rota               | Descrição                                   |
|--------|--------------------|---------------------------------------------|
| POST   | `/classify/`       | Classifica e retorna técnico + score        |
| POST   | `/debug-classify/` | Mesma resposta + payload cru da OpenAI      |

---

## Como funciona

1. **Keyword Router** (`routing/keywords.py`): regras via regex.  
2. **Finance Override** (`routing/finance.py`): override para setores financeiros.  
3. **LLM Fallback** (`routing/llm.py`): fallback para modelo finetuned.  
4. **Busca Vetorial**: gera embedding + consulta Qdrant na coleção correspondente.

---

## Testes

```bash
python -m pytest -q
```

---

## Licença

MIT

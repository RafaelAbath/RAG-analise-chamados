# True Auditoria – RAG de Chamados

Retrieval-Augmented Generation que **classifica e roteia** chamados internos para o técnico correto.  
Baseada em **FastAPI + OpenAI + Qdrant** e empacotada em Docker.

---

##  Novidades (v1.1)

* **Coleções separadas no Qdrant** – além da coleção `tecnicos`, agora existe `nip_reclames` para setores que contêm NIP/Reclames.
* **Roteamento por palavras-chave** – `router_rules.py` decide o setor antes de consultar o LLM:
  | Caso detectado | Setor forçado |
  |---------------|---------------|
  | `OPME` **e** (`ANS`\|`NIP`\|`Judicial`\|`Reclame`) | `NIP Reclames e judiciais OPME` |
  | `Home Care` **e** (`ANS`\|`NIP`\|`Judicial`\|`Reclame`) | `NIP Reclames e judiciais HC` |
  | Apenas `OPME` | `OPME` |
  | Apenas `ANS`/`NIP` | `Judiciais + NIPs` |

* **Endpoint protegido** – todas as rotas exigem o cabeçalho `X-API-KEY`.

---

##  Estrutura

```
app/
├─ ingest_data.py      # indexação de vetores nos Qdrant collections
├─ main.py             # API FastAPI
├─ router_rules.py     # regex → setor
├─ requirements.txt    # dependecias do projeto

Dockerfile             # imagem slim Python 3.11
README.md              # este arquivo
requirements.txt       # deps de runtime
tecnicos_secoes.csv    # base de técnicos/áreas
```

---

##   Variáveis de Ambiente (.env)

```dotenv
# OpenAI
OPENAI_API_KEY=
FINETUNED_MODEL=ft-...
EMBEDDING_MODEL=text-embedding-ada-002

# Qdrant
QDRANT_URL=http://qdrant:6333       # ou URL externa
QDRANT_API_KEY=                    # opcional se self-host
QDRANT_COLLECTION=tecnicos         # coleção default
QDRANT_COLLECTION_NIP=nip_reclames # coleção para NIP/Reclames

# API FastAPI
API_KEY=super-secreta              # usada no header X-API-KEY
```

---

##   Execução rápida (Docker Compose)

```bash
git clone https://github.com/<user>/true-auditoria-rag.git
cd true-auditoria-rag
cp .env.example .env   # edite as chaves

# Sobe API (porta 8000) e Qdrant (opcional, comente qdrant: no compose)
docker compose up --build -d

# Ingestão inicial (gera embeddings e popula as duas coleções)
docker compose exec api python ingest_data.py
```

---

## 🔌  Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/classify/` | Retorna o setor escolhido pela IA, técnico responsável e score de similaridade |
| `POST` | `/debug-classify/` | Mesmo retorno + payload cru da OpenAI (debug) |

### Exemplo de requisição

```bash
curl -X POST http://localhost:8000/classify/      -H "Content-Type: application/json"      -H "X-API-KEY: $API_KEY"      -d '{"titulo": "Reclamação ANS sobre OPME", "descricao": "Beneficiário queixou-se do prazo de resposta"}'
```

Resposta:
```json
{
  "setor_ia": "NIP Reclames e judiciais OPME",
  "tecnico_id": 17,
  "tecnico_nome": "TRUE – HIDINES ALFRADIQUE DE MOURA JUNIOR",
  "tecnico_setor": "NIP Reclames e judiciais OPME",
  "confianca": 0.82
}
```

---

##   Como funciona

1. **Keyword router** (`router_rules.py`)
   * Regex verifica combinações de `ANS`, `OPME`, `Home Care`, etc.
   * Se casar, devolve o setor diretamente.
2. **LLM fallback**
   * Caso nenhum regex case, `main.py` pergunta ao modelo finetuned qual setor é o melhor.
3. **Busca vetorial**
   * Cria embedding com responsabilidades + exemplos + texto do chamado.
   * Consulta **a coleção correta** (`tecnicos` ou `nip_reclames`) filtrando (`match`) pelo setor.
4. **Retorno** com o técnico e score de similaridade.

---

##   Testes rápidos

```bash
python -m pytest -q    # inclui testes de regex no pacote tests/
```

---

##   Licença

MIT.

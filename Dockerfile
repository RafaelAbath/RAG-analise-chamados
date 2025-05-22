FROM python:3.11-slim

WORKDIR /app

# 1) Copia o requirements.txt que está na raiz
COPY requirements.txt .

# 2) Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copia todo o seu código da pasta `app/` para /app
COPY app/. .

# 4) Copia o CSV de técnicos
COPY data/. data/

# 5) Expõe e inicia o Uvicorn apontando para app/api/main.py
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

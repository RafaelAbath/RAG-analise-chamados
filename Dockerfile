FROM python:3.11-slim
WORKDIR /app

# 1. Copia e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copia o seu código (assegura que /app/core/config.py é o atualizado)
COPY app/ .

# 3. Copia os dados
COPY data/ ./data

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

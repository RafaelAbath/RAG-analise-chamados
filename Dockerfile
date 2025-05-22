# Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o pacote da aplicação (core/, api/, routing/, services/)
COPY app/ .

# Copia a pasta de dados
COPY data/ ./data

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

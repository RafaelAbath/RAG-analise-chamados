FROM python:3.11-slim

WORKDIR /app


ENV PYTHONPATH=/app

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY app/. .


COPY data/. data/


CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

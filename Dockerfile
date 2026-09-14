# =============================================================================
# MausamNetra — single consolidated Dockerfile for every Python service.
# Shared by: backend, classifier, verification, ingestion, pipeline-worker.
# docker-compose.yml overrides `working_dir` + `command` per service.
# =============================================================================
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY ml ./ml
COPY ingestion ./ingestion
COPY integration ./integration
COPY data ./data
COPY main.py .

RUN mkdir -p backend/uploads/images backend/uploads/videos

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8001

WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
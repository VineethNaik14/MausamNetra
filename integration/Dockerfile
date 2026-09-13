FROM python:3.11-slim

WORKDIR /app

COPY ingestion_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY integration ./integration

CMD ["python", "-m", "integration.pipeline_worker", "--mode", "kafka"]

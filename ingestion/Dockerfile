FROM python:3.11-slim

WORKDIR /app

COPY ingestion_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ingestion ./ingestion
COPY data ./data

# Default: continuous realtime simulation, publishing to Kafka (weather.cleaned).
CMD ["python", "-m", "ingestion.realtime_demo", "--interval", "3"]

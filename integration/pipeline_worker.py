"""End-to-end bridge: weather.cleaned (Member 2) -> classifier (Member 3)
-> verification (Member 4).

This is the piece that did not belong to any single member: Member 2
publishes cleaned reports, Member 3 and Member 4 each expose an
independent FastAPI microservice, and something has to call them in
order and hand the merged result onward (to Member 5's backend, once it
exists). That "something" is this file.

Two modes:

1. ``--mode demo``  (default, no Kafka/services required to *start* the
   script, but the classifier + verification services must be running)
   Sends ONE sample citizen report through the full pipeline. This is
   the fastest way to prove the September 12 integration milestone:

       INGEST -> CLASSIFY -> VERIFY

2. ``--mode kafka``  Consumes continuously from the real
   ``weather.cleaned`` Kafka topic that Member 2's producer publishes
   to, so this becomes the always-on integration worker once Kafka is
   up (``docker compose up -d``).

Usage
-----
    # start the two ML services first (see README / docker-compose)
    python -m integration.pipeline_worker --mode demo
    python -m integration.pipeline_worker --mode kafka
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import requests

from integration.schema_adapter import (
    apply_classification,
    to_classifier_request,
    to_normalized_weather_report,
    to_related_reports,
)

CLASSIFIER_URL = os.getenv("CLASSIFIER_URL", "http://localhost:8000")
VERIFICATION_URL = os.getenv("VERIFICATION_URL", "http://localhost:8001")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_CLEANED", "weather.cleaned")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")


def classify(report: Dict[str, Any]) -> Dict[str, Any]:
    payload = to_classifier_request(report)
    resp = requests.post(f"{CLASSIFIER_URL}/classify", json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()


def verify(report: Dict[str, Any], related: list[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    payload = {
        "report": to_normalized_weather_report(report),
        "related_reports": to_related_reports(related or []),
    }
    resp = requests.post(f"{VERIFICATION_URL}/api/v1/verification/verify", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def process_one(report: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single canonical WeatherReport dict through classify -> verify."""
    print(f"[1/3] INGESTED    -> report_id={report['id']} source={report.get('source')}")

    classification = classify(report)
    report = apply_classification(report, classification)
    print(
        f"[2/3] CLASSIFIED  -> event_type={report['event_type']} "
        f"confidence={report['event_confidence']:.2f}"
    )

    result = verify(report)
    print(
        f"[3/3] VERIFIED    -> trust_score={result['trust_score']} "
        f"status={result['status']}"
    )

    merged = {**report, "verification": result}
    return merged


def run_demo() -> None:
    """No Kafka needed: pushes one sample citizen report through the pipeline.

    Mirrors ingestion/demo.py's sample so the two demos can be compared
    side by side.
    """
    sample = {
        "id": "demo-0001",
        "source": "citizen",
        "source_type": "citizen_report",
        "text": "Heavy rainfall has caused severe waterlogging near Hebbal.",
        "event_type": None,
        "event_confidence": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": 13.0358,
        "longitude": 77.5970,
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "media_url": "image01.jpg",
        "metadata": {},
    }

    print("=" * 72)
    print("MAUSAMNETRA — INGESTION -> CLASSIFICATION -> VERIFICATION (DEMO)")
    print("=" * 72)
    merged = process_one(sample)

    print("\nFinal merged record (ready for Member 5 backend / DB):")
    print(json.dumps(merged, indent=2, default=str))


def run_kafka() -> None:
    if not KAFKA_BOOTSTRAP:
        print("[WORKER] KAFKA_BOOTSTRAP_SERVERS is not set; falling back to --mode demo.")
        run_demo()
        return

    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        api_version=(2, 5, 0),
    )
    print(f"[WORKER] Listening on {KAFKA_TOPIC}, classifying + verifying each report...")

    try:
        for message in consumer:
            report = message.value
            try:
                merged = process_one(report)
                print(json.dumps(merged, indent=2, default=str))
            except requests.RequestException as exc:
                print(f"[WORKER] Downstream service error for report_id={report.get('id')}: {exc}")
    except KeyboardInterrupt:
        print("\n[WORKER] Stopped by user")
    finally:
        consumer.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "kafka"], default="demo")
    args = parser.parse_args()

    if args.mode == "demo":
        run_demo()
    else:
        run_kafka()


if __name__ == "__main__":
    main()

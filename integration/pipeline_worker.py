"""Bridge: weather.cleaned (Member 2's Kafka topic) -> your backend's
POST /api/v1/reports.

Classification and verification are NOT done here anymore — your
backend's ReportService already calls the real classifier/trust-engine/
duplicate-detector adapters for every report it receives, so forwarding
the raw report and letting it run through that same pipeline avoids
classifying/verifying twice.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, Optional

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_CLEANED", "weather.cleaned")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")

# Ingestion's report["source"] strings line up with the backend's
# SourceType enum for everything except "dataset", which the backend
# doesn't have a dedicated source for — closest existing match is the
# "Regional News Feed" (NEWS) source, mirroring schema_adapter.py's own
# "dataset" -> "verified_news" mapping.
#
# "IMD" and "GDELT" are the two optional real-data adapters added in the
# MausamRakshak V2 ingestion module (ingestion/imd/client.py,
# ingestion/web/gdelt_client.py). Both build WeatherReport objects directly
# instead of going through cleaner.normalize_source, so they emit these
# exact literal, uppercase strings rather than a lowercase/underscored
# alias. They map onto the backend's seeded "Govt Disaster Cell"
# (GOVERNMENT) and "Regional News Feed" (NEWS) sources respectively so
# that, once a team member configures IMD_API_KEY or wires up the GDELT
# poller, reports don't silently fall through to the "citizen" default.
_SOURCE_TYPE_MAP = {
    "citizen": "citizen",
    "weather_api": "weather_api",
    "public_feed": "public_feed",
    "simulated_social": "simulated_social",
    "dataset": "news",
    "IMD": "government",
    "GDELT": "news",
}

_source_id_cache: Dict[str, str] = {}


def _load_source_ids() -> None:
    """Fetch active sources once and index by SourceType."""
    resp = requests.get(f"{BACKEND_URL}/api/v1/sources", timeout=5)
    resp.raise_for_status()
    for source in resp.json()["data"]:
        _source_id_cache[source["type"]] = source["id"]


def _resolve_source_id(report_source: str) -> Optional[str]:
    if not _source_id_cache:
        _load_source_ids()
    source_type = _SOURCE_TYPE_MAP.get(report_source, "citizen")
    return _source_id_cache.get(source_type)


def submit_to_backend(report: Dict[str, Any]) -> Dict[str, Any]:
    source_id = _resolve_source_id(report.get("source", ""))
    if source_id is None:
        raise RuntimeError(f"No backend source configured for '{report.get('source')}'")

    payload = {
        "source_id": source_id,
        "text": report.get("text", ""),
        "latitude": report["latitude"],
        "longitude": report["longitude"],
        "city": report.get("city"),
        "district": report.get("district"),
        "state": report.get("state"),
        "media_url": report.get("media_url"),
        "timestamp": report.get("timestamp"),
        "report_metadata": report.get("metadata") or None,
    }
    resp = requests.post(f"{BACKEND_URL}/api/v1/reports", json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def process_one(report: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[1/2] INGESTED -> id={report.get('id')} source={report.get('source')}")
    result = submit_to_backend(report)
    created = result["data"]
    print(
        f"[2/2] SUBMITTED -> backend report_id={created['id']} "
        f"status={created['status']} event_type={created.get('event_type')}"
    )
    return created


def run_demo() -> None:
    from datetime import datetime, timezone

    sample = {
        "id": "demo-0001",
        "source": "citizen",
        "text": "Heavy rainfall has caused severe waterlogging near Hebbal.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": 13.0358,
        "longitude": 77.5970,
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "media_url": None,
        "metadata": {},
    }
    print("=" * 72)
    print("MAUSAMNETRA — INGESTION -> BACKEND (DEMO)")
    print("=" * 72)
    process_one(sample)

def run_simulate(count: int, interval: float) -> None:
    """Generate synthetic social-media-style reports and POST them straight
    to the backend, without needing Kafka running at all. Best option for a
    live demo: judges watch reports appear on the dashboard in real time."""
    from ingestion.social_simulator.simulator import generate_reports

    print(f"[WORKER] Simulating {count or 'unlimited'} reports, {interval}s apart -> {BACKEND_URL}")
    try:
        for report in generate_reports(None if count == 0 else count):
            try:
                process_one(report)
            except requests.RequestException as exc:
                print(f"[WORKER] Backend error for report_id={report.get('id')}: {exc}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[WORKER] Stopped by user")
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
    print(f"[WORKER] Listening on {KAFKA_TOPIC}, forwarding each report to {BACKEND_URL}...")

    try:
        for message in consumer:
            report = message.value
            try:
                process_one(report)
            except requests.RequestException as exc:
                print(f"[WORKER] Backend error for report_id={report.get('id')}: {exc}")
    except KeyboardInterrupt:
        print("\n[WORKER] Stopped by user")
    finally:
        consumer.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "kafka", "simulate"], default="demo")
    parser.add_argument("--count", type=int, default=0, help="0 = run forever (simulate mode)")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between reports (simulate mode)")
    args = parser.parse_args()
    if args.mode == "demo":
        run_demo()
    elif args.mode == "simulate":
        run_simulate(args.count, args.interval)
    else:
        run_kafka()


if __name__ == "__main__":
    main()
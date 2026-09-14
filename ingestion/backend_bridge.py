"""Bridges normalized ingestion reports into the real backend.

Every other file in this package (demo.py, streaming/consumer.py,
citizen_reports/api.py) produces a normalized ``WeatherReport`` (see
schemas.py) but stops there - none of them actually deliver it anywhere
the AI pipeline, database, or dashboard can see it. This module is that
missing last hop: it looks up the right Source row via the backend's own
``GET /api/v1/sources`` and posts the report to
``POST /api/v1/reports`` using the exact contract in
mausamnetra_backend/app/schemas/report.py::ReportCreate.

Usage:
    from ingestion.backend_bridge import push_report

    report = ingest_citizen_report(raw_payload)   # -> WeatherReport
    result = push_report(report)                  # -> backend's ReportRead dict, or None on failure
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional, Union

import requests

from .schemas import WeatherReport

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("BACKEND_BRIDGE_TIMEOUT", "10"))

# Maps this pipeline's source_type strings (see normalizer.py / demo.py /
# social_simulator/simulator.py / weather_api/client.py / web/gdelt_client.py)
# to the Source.name rows created by mausamnetra_backend/scripts/seed.py.
# If your deployment uses different source names, override via
# SOURCE_TYPE_MAP env var (JSON) or edit this dict directly.
_DEFAULT_SOURCE_TYPE_MAP = {
    "citizen_report": "Citizen App",
    "weather_api": "IMD Weather API",
    "simulated_social": "Simulated Social Stream",
    "simulated_public_feed": "Public Social Feed",
    "web_news": "Regional News Feed",
}


class BridgeError(RuntimeError):
    """Raised when a report can't be delivered to the backend."""


@lru_cache(maxsize=1)
def _source_name_to_id() -> Dict[str, str]:
    """Fetch active sources from the backend once and cache name -> id."""
    resp = requests.get(f"{BACKEND_URL}/sources", timeout=REQUEST_TIMEOUT_SECONDS)
    resp.raise_for_status()
    body = resp.json()
    sources = body.get("data", body)  # ApiResponse envelope wraps it in "data"
    return {s["name"]: s["id"] for s in sources}


def resolve_source_id(source_type: str) -> str:
    """Map an ingestion source_type to a backend Source UUID.

    Raises BridgeError if the backend has no matching active source -
    run `python scripts/seed.py` in mausamnetra_backend first, or add
    the mapping to _DEFAULT_SOURCE_TYPE_MAP / SOURCE_TYPE_MAP.
    """
    source_name = _DEFAULT_SOURCE_TYPE_MAP.get(source_type, source_type)
    try:
        name_to_id = _source_name_to_id()
    except requests.RequestException as exc:
        raise BridgeError(
            f"Could not reach backend at {BACKEND_URL}/sources: {exc}"
        ) from exc

    source_id = name_to_id.get(source_name)
    if source_id is None:
        raise BridgeError(
            f"No active backend source named '{source_name}' (mapped from "
            f"source_type='{source_type}'). Known sources: {list(name_to_id)}. "
            "Run `python scripts/seed.py` in mausamnetra_backend, or fix the mapping."
        )
    return source_id


def _to_report_create_payload(report: WeatherReport, source_id: str) -> Dict[str, Any]:
    """Build the exact JSON body ReportCreate expects."""
    return {
        "source_id": source_id,
        "text": report.text,
        "timestamp": report.timestamp.isoformat(),
        "latitude": report.latitude,
        "longitude": report.longitude,
        "city": report.city,
        "district": report.district,
        "state": report.state,
        "media_url": report.media_url,
        "report_metadata": report.metadata or None,
    }


def push_report(
    report: Union[WeatherReport, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Post a normalized report to the backend. Accepts either a WeatherReport
    instance or the dict form (e.g. ingest_citizen_report(...) and the
    Kafka consumer both hand back plain dicts via .model_dump()).

    Returns the created ReportRead dict on success, or None if delivery
    failed (error is logged, not raised, so a single bad report doesn't
    kill a batch/stream job)."""
    if isinstance(report, dict):
        report = WeatherReport.model_validate(report)

    try:
        source_id = resolve_source_id(report.source_type)
        payload = _to_report_create_payload(report, source_id)
        resp = requests.post(
            f"{BACKEND_URL}/reports", json=payload, timeout=REQUEST_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        body = resp.json()
        print(
            f"[BRIDGE] delivered report {report.id} -> backend report {body['data']['id']}"
        )
        return body.get("data", body)
    except (BridgeError, requests.RequestException) as exc:
        print(f"[BRIDGE] failed to deliver report {report.id}: {exc}")
        return None

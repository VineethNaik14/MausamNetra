"""Translates Member 2's canonical ``WeatherReport`` (ingestion/schemas.py)
into the request shapes Member 3 (classification) and Member 4
(verification) already expect.

Why this file exists
---------------------
Both ML modules were built independently and validated against slightly
different field names than the ingestion contract in
``docs/integration_contract.json``:

    ingestion.WeatherReport        ml.verification.NormalizedWeatherReport
    -------------------------      --------------------------------------
    id                       -->   report_id
    source: str ("citizen")  -->   source: ReportSource enum ("citizen")
    media_url: str | None    -->   media: MediaAsset | None

Nothing in either teammate's module needs to change to fix this — it is
a pure boundary-translation concern, which is exactly what an
integration layer should own.
"""
from __future__ import annotations

from typing import Any, Dict, List

# Source strings Member 2's cleaner.py can emit (see ingestion/cleaner.py
# SOURCE_ALIASES) mapped onto Member 4's ReportSource enum values. Any
# source not listed here already degrades safely to UNKNOWN inside
# ReportSource._missing_, but we map the known ones explicitly so trust
# scoring isn't silently penalized for sources we DO recognize.
SOURCE_MAP = {
    "citizen": "citizen",
    "weather_api": "weather_api",
    "dataset": "verified_news",       # historical/government-style dataset records
    "public_feed": "social_media",
    "simulated_social": "social_media",
}


def to_classifier_request(report: Dict[str, Any]) -> Dict[str, Any]:
    """Build the payload for POST /classify (ml/classification/api/main.py)."""
    return {
        "report_id": report["id"],
        "text": report.get("text", ""),
    }


def apply_classification(report: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
    """Merge classifier output back into the canonical report (Member 3's
    fields per integration_contract.json ownership block)."""
    merged = dict(report)
    merged["event_type"] = classification["event_type"]
    merged["event_confidence"] = classification["confidence"]
    return merged


def to_normalized_weather_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Build the payload for POST /api/v1/verification/verify's `report` field
    (ml/verification/schemas/report.py: NormalizedWeatherReport)."""
    media = None
    if report.get("media_url"):
        media = {"url": report["media_url"]}

    return {
        "report_id": report["id"],
        "source": SOURCE_MAP.get(report.get("source", ""), "unknown"),
        "text": report.get("text"),
        "event_type": report.get("event_type"),
        "event_confidence": report.get("event_confidence"),
        "latitude": report.get("latitude"),
        "longitude": report.get("longitude"),
        "city": report.get("city"),
        "district": report.get("district"),
        "state": report.get("state"),
        "timestamp": report.get("timestamp"),
        "media": media,
    }


def to_related_reports(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build RelatedReport payloads (for cross-source corroboration) from a
    list of other canonical WeatherReport dicts, e.g. other reports already
    seen nearby in time/space. Until Member 5's PostGIS-backed
    VerificationRepository exists, the caller supplies these manually or
    passes an empty list — the verification engine works fine either way,
    just with a lower cross-source-agreement component."""
    related = []
    for c in candidates:
        related.append(
            {
                "report_id": c["id"],
                "source": SOURCE_MAP.get(c.get("source", ""), "unknown"),
                "text": c.get("text"),
                "event_type": c.get("event_type"),
                "latitude": c.get("latitude"),
                "longitude": c.get("longitude"),
                "timestamp": c.get("timestamp"),
            }
        )
    return related

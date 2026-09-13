from typing import Any, Dict

from ..normalizer import normalize_record


def ingest_citizen_report(payload: Dict[str, Any]) -> dict:
    """Normalize a citizen-submitted weather report."""
    payload = dict(payload)
    payload.setdefault("source", "citizen")
    payload.setdefault("source_type", "citizen_report")
    return normalize_record(payload).model_dump(mode="json")

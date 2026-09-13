from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from pydantic import ValidationError

from .cleaner import clean_raw_record
from .schemas import WeatherReport


def parse_timestamp(value: Any) -> datetime:
    """Parse common ISO timestamps and normalize them to UTC."""
    if value is None or str(value).strip() == "":
        raise ValueError("missing_timestamp")

    raw = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_record(raw: Dict[str, Any]) -> WeatherReport:
    """Convert a heterogeneous source record into the common report contract."""
    cleaned, errors = clean_raw_record(raw)
    if errors:
        raise ValueError(", ".join(errors))

    try:
        latitude = float(cleaned["latitude"])
        longitude = float(cleaned["longitude"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid_coordinates") from exc

    metadata = dict(cleaned.get("metadata") or {})

    # Member 3 owns final event classification. Preserve source labels without
    # forcing them into the classifier-owned fields.
    if cleaned.get("event_type"):
        metadata["source_event_type"] = cleaned["event_type"]

    return WeatherReport(
        id=str(cleaned.get("id") or uuid4()),
        source=cleaned["source"],
        source_type=str(cleaned.get("source_type") or cleaned["source"]),
        text=cleaned["text"],
        event_type=None,
        event_confidence=None,
        timestamp=parse_timestamp(cleaned.get("timestamp")),
        latitude=latitude,
        longitude=longitude,
        city=cleaned.get("city"),
        district=cleaned.get("district"),
        state=cleaned.get("state"),
        media_url=cleaned.get("media_url") or cleaned.get("image"),
        metadata=metadata,
    )

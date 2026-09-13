import re
from typing import Any, Dict, Tuple


SOURCE_ALIASES = {
    "citizen report": "citizen",
    "citizen": "citizen",
    "weather api": "weather_api",
    "api": "weather_api",
    "dataset": "dataset",
    "public feed": "public_feed",
    "social": "simulated_social",
    "simulated social": "simulated_social",
}


def clean_text(value: Any) -> str:
    """Normalize whitespace and remove non-printing control characters."""
    if value is None:
        return ""
    value = str(value)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", value)
    return " ".join(value.split()).strip()


def normalize_source(value: Any) -> str:
    """Map source labels to stable internal names."""
    source = clean_text(value).lower()
    return SOURCE_ALIASES.get(source, source.replace(" ", "_"))


def clean_raw_record(record: Dict[str, Any]) -> Tuple[Dict[str, Any], list[str]]:
    """Clean one record and return explicit data-quality errors."""
    cleaned = dict(record)
    errors: list[str] = []

    cleaned["text"] = clean_text(cleaned.get("text"))
    if not cleaned["text"]:
        errors.append("empty_text")

    cleaned["source"] = normalize_source(cleaned.get("source"))
    if not cleaned["source"]:
        errors.append("missing_source")

    for key in ("city", "district", "state", "media_url"):
        if cleaned.get(key) is not None:
            cleaned[key] = clean_text(cleaned[key]) or None

    return cleaned, errors

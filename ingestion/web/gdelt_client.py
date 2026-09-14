"""Real GDELT news ingestion adapter.
GDELT is a public Internet/news data source. This module does not fabricate posts.
"""
from datetime import datetime, timezone
from typing import Iterable, List
import requests
from ingestion.schemas import WeatherReport

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

DEFAULT_QUERIES = [
    '"heavy rain" India', 'flood India', 'cyclone India',
    'landslide India', 'heatwave India', 'waterlogging India', 'cloudburst India'
]


def fetch_news(query: str, max_records: int = 50) -> List[WeatherReport]:
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
        "sort": "datedesc",
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()
    reports = []
    for item in payload.get("articles", []):
        title = (item.get("title") or "").strip()
        url = item.get("url")
        if not title or not url:
            continue
        ts = _parse_time(item.get("seendate"))
        # GDELT articles do not always expose GPS. Keep location fields nullable
        # until a trusted geocoder/location extractor is connected.
        reports.append(WeatherReport(
            source="GDELT",
            source_type="web_news",
            text=title,
            timestamp=ts,
            latitude=0.0,
            longitude=0.0,
            metadata={
                "provider": "GDELT",
                "source_url": url,
                "domain": item.get("domain"),
                "language": item.get("language"),
                "query": query,
                "location_status": "not_provided_by_source",
            },
        ))
    return reports


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M%S%f"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)

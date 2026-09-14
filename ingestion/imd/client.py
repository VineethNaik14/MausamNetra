"""Official IMD API adapter.

IMD access requires credentials issued through the official IMD API platform.
No credentials are embedded in source code.
"""
import os
import requests
from ingestion.schemas import WeatherReport


def fetch_imd(endpoint: str, params: dict | None = None) -> dict:
    base = os.getenv("IMD_API_BASE_URL", "https://api.imd.gov.in/public/api")
    url = endpoint if endpoint.startswith("http") else base.rstrip("/") + "/" + endpoint.lstrip("/")
    token = os.getenv("IMD_API_KEY", "").strip()
    if not token:
        raise RuntimeError("IMD_API_KEY is not configured. Obtain access from the official IMD API portal.")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    r = requests.get(url, headers=headers, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def normalize_imd_observation(raw: dict, *, latitude: float, longitude: float,
                              city: str | None = None, state: str | None = None) -> WeatherReport:
    """Normalize a known IMD observation payload after inspecting its fields.

    IMD endpoints can expose different schemas. Keep the raw payload in metadata
    and map common observation fields when present.
    """
    obs = raw.get("data", raw)
    text = "IMD weather observation"
    measurements = {}
    for key in ("temperature", "humidity", "rainfall", "wind_speed", "wind_direction", "pressure"):
        if key in obs:
            measurements[key] = obs[key]
    if measurements:
        text += ": " + ", ".join(f"{k}={v}" for k, v in measurements.items())
    return WeatherReport(
        source="IMD",
        source_type="weather_api",
        text=text,
        timestamp=_timestamp(obs),
        latitude=latitude,
        longitude=longitude,
        city=city,
        state=state,
        metadata={"provider": "India Meteorological Department", "measurements": measurements, "raw": raw},
    )


def _timestamp(obs: dict):
    from datetime import datetime, timezone
    value = obs.get("timestamp") or obs.get("time") or obs.get("date")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)

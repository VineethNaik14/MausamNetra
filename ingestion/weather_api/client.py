import os
from datetime import datetime, timezone
from typing import Any, Dict

import requests


class GenericWeatherAPIClient:
    """Provider-neutral weather API polling client.

    Configure WEATHER_API_URL and WEATHER_API_KEY in .env.
    The response mapping can be adapted once the team selects its exact provider.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
        retries: int = 2,
    ):
        self.base_url = base_url or os.getenv("WEATHER_API_URL", "")
        self.api_key = (
            api_key if api_key is not None else os.getenv("WEATHER_API_KEY", "")
        )
        self.timeout = timeout
        self.retries = retries

    def fetch(self, latitude: float, longitude: float) -> Dict[str, Any]:
        if not self.base_url:
            raise RuntimeError("WEATHER_API_URL is not configured")

        params = {"lat": latitude, "lon": longitude}
        if self.api_key:
            params["appid"] = self.api_key

        last_error: Exception | None = None

        for attempt in range(1, self.retries + 2):
            try:
                response = requests.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                print(f"[WEATHER-API] attempt {attempt} failed: {exc}")

        raise RuntimeError(f"weather API request failed: {last_error}")


def weather_api_to_raw(
    data: Dict[str, Any],
    latitude: float,
    longitude: float,
    city: str | None = None,
    state: str | None = None,
) -> Dict[str, Any]:
    """Map common weather API response fields into Member 2's raw schema."""

    description = data.get("description")

    if not description:
        weather = data.get("weather")
        if isinstance(weather, list) and weather:
            description = weather[0].get("description")

    if not description and isinstance(data.get("current"), dict):
        current = data["current"]
        description = current.get("description")

    text = (
        description
        or data.get("text")
        or "Live weather observation received from provider"
    )

    timestamp = data.get("timestamp") or data.get("dt")
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        ).isoformat()

    timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    return {
        "source": "weather_api",
        "source_type": "weather_api",
        "text": text,
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "city": city or data.get("city") or data.get("name"),
        "state": state,
        "metadata": {"provider_payload": data},
    }

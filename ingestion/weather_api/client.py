import os
from datetime import datetime, timezone
from typing import Any, Dict

import requests


class GenericWeatherAPIClient:
    """Weather API client supporting Open-Meteo and common key-based APIs.

    Open-Meteo is the default provider because its public forecast endpoint
    requires no API key for non-commercial use.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
        retries: int = 2,
    ):
        self.base_url = base_url or os.getenv(
            "WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast"
        )
        self.api_key = (
            api_key if api_key is not None else os.getenv("WEATHER_API_KEY", "")
        )
        self.timeout = timeout
        self.retries = retries

    def _build_params(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Build provider-specific query parameters."""
        if "api.open-meteo.com" in self.base_url:
            # Open-Meteo uses latitude/longitude and returns live current
            # conditions in the `current` object. No API key is required.
            return {
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "precipitation",
                        "rain",
                        "showers",
                        "weather_code",
                        "wind_speed_10m",
                        "wind_direction_10m",
                        "wind_gusts_10m",
                    ]
                ),
                "timezone": "UTC",
            }

        # Generic fallback for APIs such as OpenWeather-style endpoints.
        params: Dict[str, Any] = {"lat": latitude, "lon": longitude}
        if self.api_key:
            params["appid"] = self.api_key
        return params

    def fetch(self, latitude: float, longitude: float) -> Dict[str, Any]:
        if not self.base_url:
            raise RuntimeError("WEATHER_API_URL is not configured")

        params = self._build_params(latitude, longitude)
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


def _open_meteo_to_raw(
    data: Dict[str, Any],
    latitude: float,
    longitude: float,
    city: str | None,
    state: str | None,
) -> Dict[str, Any]:
    """Convert Open-Meteo's current conditions into Member 2's raw schema."""
    current = data.get("current", {})
    if not isinstance(current, dict) or not current:
        raise ValueError("Open-Meteo response does not contain current conditions")

    # Keep the raw weather measurements in metadata so Member 3/4/5 can use
    # them later without changing the canonical top-level report contract.
    measurements = {
        key: current.get(key)
        for key in (
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "showers",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        )
        if key in current
    }

    weather_code = current.get("weather_code")
    text = (
        f"Live weather observation: temperature {current.get('temperature_2m')}°C, "
        f"humidity {current.get('relative_humidity_2m')}%, "
        f"precipitation {current.get('precipitation')} mm, "
        f"wind {current.get('wind_speed_10m')} km/h, "
        f"weather_code {weather_code}."
    )

    timestamp = current.get("time") or datetime.now(timezone.utc).isoformat()

    return {
        "source": "weather_api",
        "source_type": "weather_api",
        "text": text,
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "city": city,
        "state": state,
        "metadata": {
            "provider": "Open-Meteo",
            "provider_url": "https://open-meteo.com/",
            "measurements": measurements,
            "timezone": data.get("timezone"),
            "utc_offset_seconds": data.get("utc_offset_seconds"),
        },
    }


def weather_api_to_raw(
    data: Dict[str, Any],
    latitude: float,
    longitude: float,
    city: str | None = None,
    state: str | None = None,
) -> Dict[str, Any]:
    """Map common weather API response fields into Member 2's raw schema."""

    # Open-Meteo has a distinctive `current` object with weather_code and
    # temperature_2m fields. Handle it explicitly before generic mappings.
    if isinstance(data.get("current"), dict) and (
        "temperature_2m" in data["current"] or "weather_code" in data["current"]
    ):
        return _open_meteo_to_raw(data, latitude, longitude, city, state)

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

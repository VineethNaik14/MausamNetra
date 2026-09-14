"""Contract for connecting an officially authorized social-media API.

No fake social posts are generated here. Implement a provider adapter only after
obtaining the platform's permitted API credentials and respecting its terms.
"""
from typing import Protocol, Iterable
from ingestion.schemas import WeatherReport

class SocialProvider(Protocol):
    def search(self, hashtags: Iterable[str]) -> Iterable[WeatherReport]: ...

TRACKED_HASHTAGS = ["#IMD", "#WeatherAlert", "#HeavyRain", "#Flood", "#Cyclone", "#Landslide", "#Heatwave"]

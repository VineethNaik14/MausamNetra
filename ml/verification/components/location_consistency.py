"""MODULE 2 — Location consistency.

Checks whether a report's GPS coordinates are consistent with its
reported city/state, and (optionally) with other nearby reports.

Design notes:
    * No external geocoding API calls (per the project brief). A small
      offline gazetteer of major Indian cities is used as a
      PostGIS-friendly stand-in; in production this lookup would be a
      ``SELECT`` against a cities table with a PostGIS geometry column
      instead of a Python dict.
    * When the reported city isn't in the gazetteer, the component
      falls back to cross-checking against related/nearby reports
      rather than guessing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional

from ..schemas.report import NormalizedWeatherReport, RelatedReport

EARTH_RADIUS_KM = 6371.0

#: Minimal offline gazetteer (approximate city-centre coordinates).
#: Extend freely — this is intentionally small for the MVP.
_CITY_GAZETTEER: dict[str, tuple[float, float]] = {
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "hebbal": (13.0358, 77.5970),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025),
    "new delhi": (28.6139, 77.2090),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "guwahati": (26.1445, 91.7362),
    "bhubaneswar": (20.2961, 85.8245),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "patna": (25.5941, 85.1376),
    "bhopal": (23.2599, 77.4126),
    "chandigarh": (30.7333, 76.7794),
    "thiruvananthapuram": (8.5241, 76.9366),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


@dataclass(frozen=True)
class LocationConsistencyResult:
    score: float  # 0-100
    reason: str


class LocationConsistencyChecker:
    """Determines whether GPS coordinates match the reported place name."""

    def __init__(self, consistency_radius_km: float = 25.0) -> None:
        self._radius_km = consistency_radius_km

    def check(
        self,
        report: NormalizedWeatherReport,
        related_reports: Optional[Iterable[RelatedReport]] = None,
    ) -> LocationConsistencyResult:
        if not report.has_coordinates():
            return LocationConsistencyResult(
                score=40.0,
                reason="No GPS coordinates provided; location consistency cannot be fully verified",
            )

        lat, lon = report.latitude, report.longitude  # type: ignore[assignment]

        place = (report.city or report.district or report.state or "").strip().lower()
        gazetteer_point = _CITY_GAZETTEER.get(place)

        if gazetteer_point is not None:
            distance_km = haversine_km(lat, lon, *gazetteer_point)
            if distance_km <= self._radius_km:
                score = max(60.0, 100.0 - (distance_km / self._radius_km) * 40.0)
                return LocationConsistencyResult(
                    score=round(score, 2),
                    reason=(
                        f"GPS coordinates are {distance_km:.1f} km from '{report.city}', "
                        "within the expected radius"
                    ),
                )
            return LocationConsistencyResult(
                score=15.0,
                reason=(
                    f"GPS coordinates are {distance_km:.1f} km from reported place "
                    f"'{report.city}', exceeding the {self._radius_km:.0f} km consistency radius"
                ),
            )

        # Reported place isn't in the offline gazetteer — fall back to
        # cross-checking against nearby related reports, if supplied.
        if related_reports:
            nearby = [
                r for r in related_reports if r.latitude is not None and r.longitude is not None
            ]
            if nearby:
                distances = [haversine_km(lat, lon, r.latitude, r.longitude) for r in nearby]  # type: ignore[arg-type]
                closest = min(distances)
                if closest <= self._radius_km:
                    return LocationConsistencyResult(
                        score=75.0,
                        reason=(
                            f"Place name not in gazetteer, but GPS is {closest:.1f} km from "
                            "another related report's location"
                        ),
                    )
                return LocationConsistencyResult(
                    score=35.0,
                    reason=(
                        "Place name not in gazetteer, and GPS does not match related "
                        f"reports' locations (closest is {closest:.1f} km away)"
                    ),
                )

        return LocationConsistencyResult(
            score=55.0,
            reason="Reported place name is not in the reference gazetteer; treated as neutral",
        )

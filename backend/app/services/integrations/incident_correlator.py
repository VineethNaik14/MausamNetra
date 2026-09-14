"""
Incident Correlation Service.

Unlike classifier/trust_engine/duplicate_detector, this is an internal
backend responsibility (not an external AI teammate deliverable), so it
has a real rule-based MVP implementation rather than a mock. It can be
upgraded later (e.g. ML-based clustering) without changing its interface.

Rule-based MVP logic:
    A report is correlated into an existing incident if ALL of:
      1. Same event_type
      2. Within `PROXIMITY_RADIUS_KM` of the incident's location
      3. Within `TEMPORAL_WINDOW_HOURS` of the incident's start_time
    Otherwise, a new incident should be created.
"""
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Protocol

from app.core.logging import get_logger
from app.schemas.ai_integration import CorrelationCandidateIncident, CorrelationResult

logger = get_logger(__name__)

PROXIMITY_RADIUS_KM = 15.0
TEMPORAL_WINDOW_HOURS = 12


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometers."""
    r = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


class IncidentCorrelator(Protocol):
    def correlate(
        self,
        event_type: str,
        latitude: float,
        longitude: float,
        report_time: datetime,
        candidates: list[CorrelationCandidateIncident],
    ) -> CorrelationResult:
        ...


class RuleBasedIncidentCorrelationService:
    """MVP rule-based implementation of IncidentCorrelator."""

    def correlate(
        self,
        event_type: str,
        latitude: float,
        longitude: float,
        report_time: datetime,
        candidates: list[CorrelationCandidateIncident],
    ) -> CorrelationResult:
        if report_time.tzinfo is None:
            report_time = report_time.replace(tzinfo=timezone.utc)

        best_match: CorrelationCandidateIncident | None = None
        best_distance = None

        for candidate in candidates:
            if candidate.event_type != event_type:
                continue

            distance = haversine_km(latitude, longitude, candidate.latitude, candidate.longitude)
            if distance > PROXIMITY_RADIUS_KM:
                continue

            candidate_start = datetime.fromisoformat(candidate.start_time)
            if candidate_start.tzinfo is None:
                candidate_start = candidate_start.replace(tzinfo=timezone.utc)

            if abs((report_time - candidate_start)) > timedelta(hours=TEMPORAL_WINDOW_HOURS):
                continue

            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_match = candidate

        if best_match is not None:
            logger.info(
                "IncidentCorrelation: matched existing incident %s (distance=%.2fkm)",
                best_match.incident_id,
                best_distance,
            )
            return CorrelationResult(
                matched_incident_id=best_match.incident_id,
                should_create_new=False,
                reason=(
                    f"Same event_type='{event_type}', within {PROXIMITY_RADIUS_KM}km "
                    f"and {TEMPORAL_WINDOW_HOURS}h of existing incident"
                ),
            )

        return CorrelationResult(
            matched_incident_id=None,
            should_create_new=True,
            reason="No matching incident found within proximity/time window",
        )

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.incident import Incident, IncidentSeverity
from app.models.report import Report
from app.models.verification import VerificationStatus
from app.repositories.incident_repository import IncidentRepository
from app.schemas.ai_integration import CorrelationCandidateIncident
from app.schemas.incident import IncidentFilterParams, NearbyIncidentParams
from app.services.integrations.incident_correlator import IncidentCorrelator


class IncidentService:
    def __init__(self, db: Session, correlator: IncidentCorrelator):
        self.db = db
        self.repo = IncidentRepository(db)
        self.correlator = correlator

    def correlate_and_attach(self, report: Report) -> Incident:
        """
        Determine whether `report` belongs to an existing incident or should
        create a new one, then attach the report and update incident
        counters accordingly. Returns the (possibly newly created) incident.
        """
        event_type = report.event_type or "UNKNOWN"

        candidates = [
            CorrelationCandidateIncident(
                incident_id=inc.id,
                event_type=inc.event_type,
                latitude=inc.latitude,
                longitude=inc.longitude,
                start_time=inc.start_time.isoformat(),
            )
            for inc in self.repo.list_active_candidates(event_type)
        ]

        report_time = report.timestamp or datetime.now(timezone.utc)
        result = self.correlator.correlate(
            event_type=event_type,
            latitude=report.latitude,
            longitude=report.longitude,
            report_time=report_time,
            candidates=candidates,
        )

        if result.should_create_new or result.matched_incident_id is None:
            from app.repositories.report_repository import make_point

            incident = Incident(
                event_type=event_type,
                severity=IncidentSeverity.LOW,
                latitude=report.latitude,
                longitude=report.longitude,
                location=make_point(report.longitude, report.latitude),
                state=report.state,
                district=report.district,
                city=report.city,
                start_time=report_time,
                confidence=report.event_confidence,
                report_count=0,
                verified_count=0,
                suspicious_count=0,
                duplicate_count=0,
            )
            incident = self.repo.create(incident)
        else:
            incident = self.repo.get_by_id(result.matched_incident_id)
            if incident is None:
                raise NotFoundError("Matched incident not found", code="INCIDENT_NOT_FOUND")

        report.incident_id = incident.id
        self.db.add(report)

        incident.report_count += 1
        self._recompute_severity(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def _recompute_severity(self, incident: Incident) -> None:
        """Simple prototype heuristic: severity scales with corroborated report volume."""
        if incident.report_count >= 15:
            incident.severity = IncidentSeverity.SEVERE
        elif incident.report_count >= 7:
            incident.severity = IncidentSeverity.HIGH
        elif incident.report_count >= 3:
            incident.severity = IncidentSeverity.MODERATE
        else:
            incident.severity = IncidentSeverity.LOW

    def update_counters_after_verification(self, incident_id: uuid.UUID, status: VerificationStatus) -> Incident:
        incident = self.repo.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError("Incident not found", code="INCIDENT_NOT_FOUND")

        if status == VerificationStatus.VERIFIED:
            incident.verified_count += 1
        elif status == VerificationStatus.SUSPICIOUS:
            incident.suspicious_count += 1

        return self.repo.update(incident)

    def increment_duplicate_count(self, incident_id: uuid.UUID) -> None:
        incident = self.repo.get_by_id(incident_id)
        if incident is None:
            return
        incident.duplicate_count += 1
        self.repo.update(incident)

    def get_by_id(self, incident_id: uuid.UUID) -> Incident:
        incident = self.repo.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError("Incident not found", code="INCIDENT_NOT_FOUND")
        return incident

    def list_filtered(self, params: IncidentFilterParams) -> tuple[list[Incident], int]:
        return self.repo.list_filtered(
            event=params.event,
            state=params.state,
            district=params.district,
            city=params.city,
            status=params.status,
            severity=params.severity,
            page=params.page,
            page_size=params.page_size,
        )

    def list_for_map(self) -> list[Incident]:
        return self.repo.list_for_map()

    def find_nearby(self, params: NearbyIncidentParams) -> list[tuple[Incident, float]]:
        return self.repo.find_nearby(
            latitude=params.latitude,
            longitude=params.longitude,
            radius_km=params.radius_km,
            event=params.event,
            state=params.state,
            district=params.district,
            city=params.city,
        )

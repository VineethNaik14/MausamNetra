import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.duplicate import Duplicate
from app.models.report import Report, ReportStatus
from app.models.verification import Verification, VerificationStatus
from app.repositories.report_repository import ReportRepository, make_point
from app.repositories.verification_repository import VerificationRepository
from app.schemas.ai_integration import (
    CandidateReport,
    ClassifierInput,
    CorroboratingReport,
    DuplicateDetectorInput,
    TrustEngineInput,
)
from app.schemas.report import ReportCreate, ReportFilterParams
from app.services.incident_service import IncidentService
from app.services.integrations.classifier import EventClassifier
from app.services.integrations.duplicate_detector import DuplicateDetector
from app.services.integrations.trust_engine import TrustEngine
from app.services.websocket_service import WebSocketService

logger = get_logger(__name__)


class ReportService:
    """
    Orchestrates the report ingestion pipeline:

        validate -> store raw report -> classify -> trust evaluate ->
        duplicate detect -> incident correlation -> persist -> broadcast

    Resilience: if any AI step fails, the exception is caught and logged;
    the original report is NEVER lost. Its status is set to FAILED so it
    can be retried or manually reviewed later.
    """

    def __init__(
        self,
        db: Session,
        classifier: EventClassifier,
        trust_engine: TrustEngine,
        duplicate_detector: DuplicateDetector,
        incident_service: IncidentService,
        websocket_service: WebSocketService,
    ):
        self.db = db
        self.repo = ReportRepository(db)
        self.verification_repo = VerificationRepository(db)
        self.classifier = classifier
        self.trust_engine = trust_engine
        self.duplicate_detector = duplicate_detector
        self.incident_service = incident_service
        self.websocket_service = websocket_service

    def get_by_id(self, report_id: uuid.UUID) -> Report:
        report = self.repo.get_by_id(report_id)
        if report is None:
            raise NotFoundError("Report not found", code="REPORT_NOT_FOUND")
        return report

    def list_filtered(self, params: ReportFilterParams) -> tuple[list[Report], int]:
        return self.repo.list_filtered(
            event=params.event,
            state=params.state,
            district=params.district,
            city=params.city,
            status=params.status,
            source_id=params.source_id,
            date_from=params.date_from,
            date_to=params.date_to,
            page=params.page,
            page_size=params.page_size,
        )

    async def create_report(self, data: ReportCreate, source_reliability: float, source_type: str | None = None) -> Report:
        report = Report(
            source_id=data.source_id,
            text=data.text,
            timestamp=data.timestamp or datetime.now(timezone.utc),
            latitude=data.latitude,
            longitude=data.longitude,
            location=make_point(data.longitude, data.latitude),
            city=data.city,
            district=data.district,
            state=data.state,
            media_url=data.media_url,
            report_metadata=data.report_metadata,
            status=ReportStatus.PENDING,
        )
        report = self.repo.create(report)
        logger.info("Report %s created (status=PENDING)", report.id)

        try:
            await self._run_pipeline(report, source_reliability, source_type)
            report.status = ReportStatus.PROCESSED
            self.repo.update(report)
        except Exception:
            logger.exception("AI pipeline failed for report %s; report preserved as FAILED", report.id)
            report.status = ReportStatus.FAILED
            self.repo.update(report)

        return report
        
    async def _run_pipeline(self, report: Report, source_reliability: float, source_type: str | None=None) -> None:
        # 1. Event classification
        classifier_output = self.classifier.classify(
            ClassifierInput(report_id=report.id, text=report.text, media_url=report.media_url)
        )
        report.event_type = classifier_output.event_type
        report.event_confidence = classifier_output.confidence
        self.repo.update(report)

        # 2. Duplicate detection against recent same-event-type reports
        candidates = self.repo.find_recent_candidates_for_duplicate_check(event_type=report.event_type)
        candidates = [c for c in candidates if c.id != report.id]
        dup_output = self.duplicate_detector.detect(
            DuplicateDetectorInput(
                current_report=CandidateReport(
                    report_id=report.id,
                    text=report.text,
                    media_url=report.media_url,
                    latitude=report.latitude,
                    longitude=report.longitude,
                    timestamp=report.timestamp.isoformat(),
                ),
                candidate_reports=[
                    CandidateReport(
                        report_id=c.id,
                        text=c.text,
                        media_url=c.media_url,
                        latitude=c.latitude,
                        longitude=c.longitude,
                        timestamp=c.timestamp.isoformat(),
                    )
                    for c in candidates
                ],
            )
        )

        if dup_output.is_duplicate and dup_output.master_report_id:
            duplicate = Duplicate(
                report_id=report.id,
                master_report_id=dup_output.master_report_id,
                similarity_score=dup_output.similarity_score,
            )
            self.db.add(duplicate)
            self.db.commit()
            logger.info("Report %s marked as duplicate of %s", report.id, dup_output.master_report_id)

        # 3. Trust evaluation (corroborating reports = same-event-type candidates found above)
        trust_output = self.trust_engine.evaluate(
            TrustEngineInput(
                report_id=report.id,
                text=report.text,
                source_reliability=source_reliability,
                source_type=source_type,
                latitude=report.latitude,
                longitude=report.longitude,
                timestamp=report.timestamp.isoformat(),
                metadata=report.report_metadata,
                corroborating_reports=[CorroboratingReport(report_id=c.id) for c in candidates[:5]],
                has_media=bool(report.media_url),
            )
        )
        verification = Verification(
            report_id=report.id,
            trust_score=trust_output.trust_score,
            status=VerificationStatus(trust_output.status),
            reason="; ".join(trust_output.reasons) if trust_output.reasons else None,
        )
        self.verification_repo.upsert(verification)

        # 4. Incident correlation (skip for duplicates - they don't spawn/attach to incidents themselves)
        if not dup_output.is_duplicate:
            incident = self.incident_service.correlate_and_attach(report)
            self.incident_service.update_counters_after_verification(incident.id, verification.status)

            await self.websocket_service.broadcast_new_incident(
                {
                    "id": str(incident.id),
                    "event_type": incident.event_type,
                    "severity": incident.severity,
                    "status": incident.status,
                    "latitude": incident.latitude,
                    "longitude": incident.longitude,
                    "city": incident.city,
                    "state": incident.state,
                    "confidence": incident.confidence,
                    "report_count": incident.report_count,
                    "verified_count": incident.verified_count,
                    "suspicious_count": incident.suspicious_count,
                    "duplicate_count": incident.duplicate_count,
                }
            )
        else:
            # If it's a duplicate of a report already attached to an incident, bump duplicate_count.
            master = self.repo.get_by_id(dup_output.master_report_id)
            if master and master.incident_id:
                self.incident_service.increment_duplicate_count(master.incident_id)

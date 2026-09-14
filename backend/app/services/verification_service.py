import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.verification import Verification, VerificationStatus
from app.repositories.report_repository import ReportRepository
from app.repositories.verification_repository import VerificationRepository
from app.schemas.verification import ManualRejectRequest, ManualVerifyRequest
from app.services.incident_service import IncidentService
from app.services.websocket_service import WebSocketService

logger = get_logger(__name__)


class VerificationService:
    def __init__(
        self,
        db: Session,
        incident_service: IncidentService,
        websocket_service: WebSocketService,
    ):
        self.db = db
        self.report_repo = ReportRepository(db)
        self.verification_repo = VerificationRepository(db)
        self.incident_service = incident_service
        self.websocket_service = websocket_service

    def _get_or_create_verification(self, report_id: uuid.UUID) -> Verification:
        verification = self.verification_repo.get_by_report_id(report_id)
        if verification is None:
            verification = Verification(report_id=report_id, trust_score=0, status=VerificationStatus.NEEDS_REVIEW)
        return verification

    async def verify(self, report_id: uuid.UUID, admin_id: uuid.UUID, data: ManualVerifyRequest) -> Verification:
        report = self.report_repo.get_by_id(report_id)
        if report is None:
            raise NotFoundError("Report not found", code="REPORT_NOT_FOUND")

        verification = self._get_or_create_verification(report_id)
        verification.status = VerificationStatus.VERIFIED
        if data.trust_score is not None:
            verification.trust_score = data.trust_score
        elif verification.trust_score < 80:
            verification.trust_score = 80
        verification.reason = data.reason or "Manually verified by admin"
        verification.verified_by = admin_id
        verification.verified_at = datetime.now(timezone.utc)

        verification = self.verification_repo.upsert(verification)
        logger.info("Admin %s verified report %s", admin_id, report_id)

        if report.incident_id:
            self.incident_service.update_counters_after_verification(report.incident_id, VerificationStatus.VERIFIED)

        await self.websocket_service.broadcast_report_verified(
            str(report_id), str(report.incident_id) if report.incident_id else None
        )
        return verification

    async def reject(self, report_id: uuid.UUID, admin_id: uuid.UUID, data: ManualRejectRequest) -> Verification:
        report = self.report_repo.get_by_id(report_id)
        if report is None:
            raise NotFoundError("Report not found", code="REPORT_NOT_FOUND")

        verification = self._get_or_create_verification(report_id)
        verification.status = VerificationStatus.REJECTED
        verification.reason = data.reason
        verification.verified_by = admin_id
        verification.verified_at = datetime.now(timezone.utc)

        verification = self.verification_repo.upsert(verification)
        logger.info("Admin %s rejected report %s", admin_id, report_id)

        await self.websocket_service.broadcast_report_rejected(str(report_id))
        return verification

    def escalate(self, report_id: uuid.UUID, admin_id: uuid.UUID, reason: str) -> Verification:
        report = self.report_repo.get_by_id(report_id)
        if report is None:
            raise NotFoundError("Report not found", code="REPORT_NOT_FOUND")

        verification = self._get_or_create_verification(report_id)
        verification.status = VerificationStatus.NEEDS_REVIEW
        verification.reason = f"Escalated by admin: {reason}"

        verification = self.verification_repo.upsert(verification)
        logger.info("Admin %s escalated report %s for review", admin_id, report_id)
        return verification

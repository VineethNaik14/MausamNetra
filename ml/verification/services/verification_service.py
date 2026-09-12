"""Orchestrates the TrustEngine with optional persistence and related-report lookup.

This is the layer the FastAPI routes call. It is the ONLY place that may
know about ``VerificationRepository`` — the TrustEngine itself stays
database-free and independently testable.
"""
from __future__ import annotations

from typing import List, Optional

from ..config import Settings, get_settings
from ..engine.trust_engine import TrustEngine
from ..interfaces.repositories import VerificationRepository
from ..logging_config import get_logger
from ..schemas.report import NormalizedWeatherReport, RelatedReport
from ..schemas.verification import BatchVerificationResult, VerificationResult

logger = get_logger("services.verification_service")


class VerificationService:
    """Application-level orchestration around ``TrustEngine``."""

    def __init__(
        self,
        engine: TrustEngine,
        repository: Optional[VerificationRepository] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.engine = engine
        self.repository = repository
        self.settings = settings or get_settings()

    def verify_report(
        self,
        report: NormalizedWeatherReport,
        related_reports: Optional[List[RelatedReport]] = None,
        image_bytes: Optional[bytes] = None,
    ) -> VerificationResult:
        if related_reports is None and self.repository is not None:
            related_reports = self.repository.get_related_reports(
                report.report_id,
                report.latitude,
                report.longitude,
                radius_km=self.settings.corroboration_radius_km,
                window_hours=self.settings.corroboration_window_hours,
            )

        result = self.engine.verify(report, related_reports=related_reports, image_bytes=image_bytes)

        if self.repository is not None:
            try:
                self.repository.save_result(result)
            except Exception as exc:  # noqa: BLE001 - persistence failure must not break the response
                logger.error("failed_to_persist_result report_id=%s error=%s", report.report_id, exc)

        return result

    def verify_batch(self, reports: List[NormalizedWeatherReport]) -> BatchVerificationResult:
        results: List[VerificationResult] = []
        failed_ids: List[str] = []

        related_by_id = {}
        if self.repository is not None:
            for report in reports:
                try:
                    related_by_id[report.report_id] = self.repository.get_related_reports(
                        report.report_id,
                        report.latitude,
                        report.longitude,
                        radius_km=self.settings.corroboration_radius_km,
                        window_hours=self.settings.corroboration_window_hours,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("related_report_lookup_failed report_id=%s error=%s", report.report_id, exc)

        for report in reports:
            try:
                result = self.engine.verify(report, related_reports=related_by_id.get(report.report_id))
                results.append(result)
                if self.repository is not None:
                    self.repository.save_result(result)
            except Exception as exc:  # noqa: BLE001 - one bad report shouldn't fail the whole batch
                logger.error("batch_verification_failed report_id=%s error=%s", report.report_id, exc)
                failed_ids.append(report.report_id)

        return BatchVerificationResult(results=results, failed_report_ids=failed_ids)

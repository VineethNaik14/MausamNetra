"""MODULE 10 — The central TrustEngine.

Composes every component via dependency injection. The engine depends
only on interfaces (``EventClassifierProtocol``) and schemas — never on
concrete ML implementations or the database — so any single piece
(classifier, similarity backend, image hasher) can be swapped
independently.

Kept synchronous and side-effect-free (no DB writes) so it stays trivial
to unit test; the async/persistence concerns live in
``services/verification_service.py``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from ..config import Settings, get_settings
from ..exceptions import ClassifierUnavailableError
from ..interfaces.classifier import EventClassifierProtocol
from ..logging_config import get_logger
from ..schemas.report import NormalizedWeatherReport, RelatedReport
from ..schemas.verification import (
    DuplicateInfo,
    ImageDuplicateResult,
    TrustFactors,
    VerificationResult,
    VerificationStatus,
)
from ..components.image_similarity import ImageDuplicateDetector
from ..components.location_consistency import LocationConsistencyChecker
from ..components.media_consistency import MediaTextConsistencyChecker
from ..components.metadata_completeness import MetadataCompletenessScorer
from ..components.source_reliability import SourceReliabilityScorer
from ..components.suspicious_detector import SuspiciousReportDetector
from ..components.temporal_consistency import TemporalConsistencyChecker
from ..components.text_similarity import (
    CrossSourceAgreementScorer,
    DuplicateTextDetector,
    SimilarityEngine,
    build_default_similarity_engine,
)

logger = get_logger("engine.trust_engine")


class TrustEngine:
    """Central verification engine. See module docstring for design rules."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        source_reliability: Optional[SourceReliabilityScorer] = None,
        location_checker: Optional[LocationConsistencyChecker] = None,
        temporal_checker: Optional[TemporalConsistencyChecker] = None,
        similarity_engine: Optional[SimilarityEngine] = None,
        duplicate_text_detector: Optional[DuplicateTextDetector] = None,
        cross_source_scorer: Optional[CrossSourceAgreementScorer] = None,
        image_detector: Optional[ImageDuplicateDetector] = None,
        media_consistency_checker: Optional[MediaTextConsistencyChecker] = None,
        metadata_scorer: Optional[MetadataCompletenessScorer] = None,
        suspicious_detector: Optional[SuspiciousReportDetector] = None,
        classifier: Optional[EventClassifierProtocol] = None,
    ) -> None:
        self.settings = settings or get_settings()
        weights = self.settings.weights

        self.source_reliability = source_reliability or SourceReliabilityScorer()
        self.location_checker = location_checker or LocationConsistencyChecker(
            consistency_radius_km=self.settings.location_consistency_radius_km
        )
        self.temporal_checker = temporal_checker or TemporalConsistencyChecker(
            max_future_skew_minutes=self.settings.max_future_skew_minutes,
            stale_report_hours=self.settings.stale_report_hours,
            corroboration_window_hours=self.settings.corroboration_window_hours,
        )

        engine = similarity_engine or build_default_similarity_engine(
            backend=self.settings.similarity_backend,
            model_name=self.settings.sentence_transformer_model,
        )
        self.similarity_engine = engine
        self.duplicate_text_detector = duplicate_text_detector or DuplicateTextDetector(
            engine,
            duplicate_threshold=self.settings.text_similarity_threshold,
            related_threshold=self.settings.text_related_threshold,
        )
        self.cross_source_scorer = cross_source_scorer or CrossSourceAgreementScorer(engine)

        self.image_detector = image_detector or ImageDuplicateDetector(
            similarity_threshold=self.settings.image_similarity_threshold,
            max_image_size_mb=self.settings.max_image_size_mb,
        )
        self.media_consistency_checker = media_consistency_checker or MediaTextConsistencyChecker()
        self.metadata_scorer = metadata_scorer or MetadataCompletenessScorer()
        self.suspicious_detector = suspicious_detector or SuspiciousReportDetector()
        self.classifier = classifier

        self._weights = weights

    def verify(
        self,
        report: NormalizedWeatherReport,
        related_reports: Optional[Iterable[RelatedReport]] = None,
        image_bytes: Optional[bytes] = None,
        now: Optional[datetime] = None,
    ) -> VerificationResult:
        """Run the full verification pipeline for a single report."""
        related_reports = list(related_reports or [])
        reasons: List[str] = []
        degraded = False

        logger.info("verification_started report_id=%s", report.report_id)

        # --- Module 1: source reliability -------------------------------
        source_score = self.source_reliability.get_source_reliability(report.source)
        reasons.append(self.source_reliability.explain(report.source))

        # --- Module 2: location consistency -----------------------------
        location_result = self.location_checker.check(report, related_reports)
        reasons.append(location_result.reason)

        # --- Module 3: temporal consistency -------------------------------
        temporal_result = self.temporal_checker.check(report, now=now, related_reports=related_reports)
        reasons.extend(temporal_result.reasons)

        # --- Module 4: cross-source agreement ------------------------------
        cross_source_score, cross_source_reason = self.cross_source_scorer.calculate_cross_source_agreement(
            report, related_reports
        )
        reasons.append(cross_source_reason)

        # --- Module 5: duplicate text detection -----------------------------
        duplicate_info = self._run_duplicate_detection(report, related_reports)

        # --- Module 6: image duplicate detection -----------------------------
        image_duplicate_result: Optional[ImageDuplicateResult] = None
        if image_bytes is not None:
            content_type = report.media.content_type if report.media else None
            try:
                image_duplicate_result = self.image_detector.check_duplicate(
                    report.report_id, image_bytes, content_type
                )
                reasons.append(image_duplicate_result.reason)
                if image_duplicate_result.possible_duplicate and not duplicate_info.is_duplicate:
                    duplicate_info = DuplicateInfo(
                        is_duplicate=True,
                        is_related=True,
                        similarity=image_duplicate_result.similarity,
                        reason=f"Image duplicate: {image_duplicate_result.reason}",
                    )
            except Exception as exc:  # noqa: BLE001 - never let image errors crash verification
                logger.warning("image_duplicate_check_failed report_id=%s error=%s", report.report_id, exc)
                reasons.append("Image could not be processed; image checks were skipped")
                degraded = True

        # --- Classification (teammate's model, via interface) ---------------
        classification = None
        classifier_used = False
        if self.classifier is not None:
            try:
                classification = self.classifier.classify(report)
                classifier_used = True
            except ClassifierUnavailableError as exc:
                logger.warning("classifier_failure report_id=%s error=%s", report.report_id, exc)
                reasons.append("Event classification was unavailable; verification proceeded without it")
                degraded = True

        # --- Module 7: media/text consistency --------------------------------
        media_result = self.media_consistency_checker.check(report, classification, image_duplicate_result)
        reasons.extend(media_result.reasons)

        # --- Module 8: metadata completeness ----------------------------------
        metadata_result = self.metadata_scorer.score(report)
        if metadata_result.missing_required:
            reasons.append("Missing required metadata: " + ", ".join(metadata_result.missing_required))

        # --- Module 9: suspicious report detection -----------------------------
        suspicious_result = self.suspicious_detector.detect(
            source_reliability=source_score,
            location_result=location_result,
            temporal_result=temporal_result,
            cross_source_agreement=cross_source_score,
            metadata_result=metadata_result,
            image_duplicate=image_duplicate_result,
        )

        # --- Weighted trust score --------------------------------------------
        w = self._weights
        trust_score = (
            w.source_reliability * source_score
            + w.location_consistency * location_result.score
            + w.temporal_consistency * temporal_result.score
            + w.cross_source_agreement * cross_source_score
            + w.media_text_consistency * media_result.score
            + w.metadata_completeness * metadata_result.score
        )
        trust_score = round(max(0.0, min(100.0, trust_score)), 2)

        status = self._decide_status(trust_score)

        result = VerificationResult(
            report_id=report.report_id,
            trust_score=trust_score,
            status=status,
            factors=TrustFactors(
                source_reliability=source_score,
                location_consistency=location_result.score,
                temporal_consistency=temporal_result.score,
                cross_source_agreement=cross_source_score,
                media_text_consistency=media_result.score,
                metadata_completeness=metadata_result.score,
            ),
            reasons=reasons,
            duplicate=duplicate_info,
            suspicious=suspicious_result,
            classifier_used=classifier_used,
            degraded=degraded,
        )

        logger.info(
            "verification_completed report_id=%s trust_score=%.2f status=%s",
            report.report_id,
            trust_score,
            status.value if hasattr(status, "value") else status,
        )
        if suspicious_result.is_suspicious:
            logger.info("suspicious_report_detected report_id=%s", report.report_id)
        if duplicate_info.is_duplicate:
            logger.info("duplicate_detected report_id=%s", report.report_id)

        return result

    def verify_batch(
        self,
        reports: Iterable[NormalizedWeatherReport],
        related_reports_by_id: Optional[dict[str, List[RelatedReport]]] = None,
    ) -> List[VerificationResult]:
        """Verify multiple reports, fitting the similarity vectorizer once.

        Fitting the TF-IDF vectorizer over the whole batch up-front avoids
        refitting per-pair, which would otherwise make batch verification
        needlessly slow.
        """
        reports = list(reports)
        related_reports_by_id = related_reports_by_id or {}

        fit_corpus = getattr(self.similarity_engine, "fit_corpus", None)
        if callable(fit_corpus):
            texts = [r.text for r in reports if r.text]
            for related in related_reports_by_id.values():
                texts.extend(r.text for r in related if r.text)
            fit_corpus(texts)

        return [
            self.verify(report, related_reports=related_reports_by_id.get(report.report_id, []))
            for report in reports
        ]

    def _run_duplicate_detection(
        self, report: NormalizedWeatherReport, related_reports: List[RelatedReport]
    ) -> DuplicateInfo:
        if not related_reports or not report.text:
            return DuplicateInfo(is_duplicate=False, is_related=False, similarity=0.0)

        match = self.duplicate_text_detector.find_best_match(report, related_reports)
        if match is None:
            return DuplicateInfo(is_duplicate=False, is_related=False, similarity=0.0)

        candidate, comparison = match
        if comparison.relation == "duplicate":
            return DuplicateInfo(
                is_duplicate=True,
                is_related=True,
                master_report_id=candidate.report_id,
                similarity=comparison.similarity,
                reason=f"Text is highly similar to report '{candidate.report_id}'",
            )
        if comparison.relation == "related":
            return DuplicateInfo(
                is_duplicate=False,
                is_related=True,
                master_report_id=candidate.report_id,
                similarity=comparison.similarity,
                reason=f"Text is related to (but not a duplicate of) report '{candidate.report_id}'",
            )
        return DuplicateInfo(is_duplicate=False, is_related=False, similarity=comparison.similarity)

    def _decide_status(self, trust_score: float) -> VerificationStatus:
        if trust_score >= self.settings.verified_threshold:
            return VerificationStatus.VERIFIED
        if trust_score >= self.settings.review_threshold:
            return VerificationStatus.NEEDS_REVIEW
        return VerificationStatus.SUSPICIOUS

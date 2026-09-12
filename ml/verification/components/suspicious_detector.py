"""MODULE 9 — Suspicious report detection.

Aggregates signals already computed by the other components into an
explainable suspicious/not-suspicious decision. Never returns a bare
boolean — every "suspicious" verdict comes with concrete reasons.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..schemas.verification import ImageDuplicateResult, SuspiciousReportResult
from .location_consistency import LocationConsistencyResult
from .metadata_completeness import MetadataCompletenessResult
from .temporal_consistency import TemporalConsistencyResult


@dataclass(frozen=True)
class SuspiciousDetectorThresholds:
    low_source_reliability: float = 30.0
    low_location_consistency: float = 30.0
    low_temporal_consistency: float = 40.0
    low_cross_source_agreement: float = 35.0
    low_metadata_completeness: float = 40.0


class SuspiciousReportDetector:
    """Combines factor scores into an explainable suspicious-report verdict."""

    def __init__(self, thresholds: Optional[SuspiciousDetectorThresholds] = None) -> None:
        self._thresholds = thresholds or SuspiciousDetectorThresholds()

    def detect(
        self,
        source_reliability: float,
        location_result: LocationConsistencyResult,
        temporal_result: TemporalConsistencyResult,
        cross_source_agreement: float,
        metadata_result: MetadataCompletenessResult,
        image_duplicate: Optional[ImageDuplicateResult],
    ) -> SuspiciousReportResult:
        reasons: List[str] = []
        t = self._thresholds

        if source_reliability < t.low_source_reliability:
            reasons.append(f"Low source reliability ({source_reliability:.0f}/100)")

        if location_result.score < t.low_location_consistency:
            reasons.append(f"Location inconsistency: {location_result.reason}")

        if temporal_result.score < t.low_temporal_consistency:
            reasons.append("Timestamp inconsistency: " + "; ".join(temporal_result.reasons))

        if cross_source_agreement < t.low_cross_source_agreement:
            reasons.append(f"No independent corroborating reports (score {cross_source_agreement:.0f}/100)")

        if metadata_result.missing_required:
            reasons.append(
                "Missing required metadata: " + ", ".join(metadata_result.missing_required)
            )

        if image_duplicate is not None and image_duplicate.possible_duplicate:
            reasons.append(f"Image appears to have been reused: {image_duplicate.reason}")

        is_suspicious = len(reasons) >= 2  # require multiple corroborating red flags
        return SuspiciousReportResult(is_suspicious=is_suspicious, reasons=reasons)

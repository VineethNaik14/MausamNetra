"""MODULE 7 — Media/text consistency.

For the MVP this is a configurable rule-based check combining:
    * whether media is attached at all
    * whether the image was flagged as a possible duplicate/reuse
    * whether the report's stated ``event_type`` agrees with the
      teammate's classifier output (consumed purely as data — this
      module has no knowledge of how classification works)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..schemas.classification import EventClassificationResult
from ..schemas.report import NormalizedWeatherReport
from ..schemas.verification import ImageDuplicateResult


@dataclass(frozen=True)
class MediaConsistencyResult:
    score: float  # 0-100
    reasons: List[str]


class MediaTextConsistencyChecker:
    """Rule-based media/text agreement scorer."""

    def check(
        self,
        report: NormalizedWeatherReport,
        classification: Optional[EventClassificationResult],
        image_duplicate: Optional[ImageDuplicateResult],
    ) -> MediaConsistencyResult:
        reasons: List[str] = []
        score = 70.0  # neutral baseline when there's nothing to check against

        has_media = report.has_media()
        if not has_media:
            reasons.append("No media attached; media/text consistency treated as neutral")
            score = 60.0
        else:
            score = 75.0
            reasons.append("Media is attached")

            if image_duplicate is not None:
                if image_duplicate.possible_duplicate:
                    score -= 30.0
                    reasons.append(f"Image flagged as possibly reused: {image_duplicate.reason}")
                else:
                    score += 10.0
                    reasons.append("Attached image does not match previously seen images")

        if classification is not None and report.event_type:
            if classification.event_type.lower() == report.event_type.lower():
                score += 15.0 * classification.confidence
                reasons.append(
                    f"Classifier agrees with reported event type '{report.event_type}' "
                    f"(confidence {classification.confidence:.2f})"
                )
            else:
                score -= 25.0
                reasons.append(
                    f"Classifier predicted '{classification.event_type}' but report states "
                    f"'{report.event_type}'"
                )
        elif classification is None:
            reasons.append("Event classification unavailable; skipped agreement check")

        score = max(0.0, min(100.0, score))
        return MediaConsistencyResult(score=round(score, 2), reasons=reasons)

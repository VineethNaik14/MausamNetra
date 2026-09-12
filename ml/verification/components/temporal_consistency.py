"""MODULE 3 — Temporal consistency.

Flags (without automatically condemning) timestamp problems:
    * impossible/future report timestamps
    * media captured well before the report was filed
    * large disagreement with corroborating reports' timestamps

An old photo does not automatically mean a fake report — the score is
lowered and the reason is explained, leaving the final call to the
decision policy / a human reviewer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from ..schemas.report import NormalizedWeatherReport, RelatedReport


@dataclass(frozen=True)
class TemporalConsistencyResult:
    score: float  # 0-100
    reasons: List[str]


class TemporalConsistencyChecker:
    """Evaluates whether a report's timestamps are internally consistent."""

    def __init__(
        self,
        max_future_skew_minutes: float = 10.0,
        stale_report_hours: float = 72.0,
        media_stale_hours: float = 24.0,
        corroboration_window_hours: float = 12.0,
    ) -> None:
        self._max_future_skew = timedelta(minutes=max_future_skew_minutes)
        self._stale_report = timedelta(hours=stale_report_hours)
        self._media_stale = timedelta(hours=media_stale_hours)
        self._corroboration_window = timedelta(hours=corroboration_window_hours)

    def check(
        self,
        report: NormalizedWeatherReport,
        now: Optional[datetime] = None,
        related_reports: Optional[Iterable[RelatedReport]] = None,
    ) -> TemporalConsistencyResult:
        now = now or datetime.now(report.timestamp.tzinfo)
        score = 100.0
        reasons: List[str] = []

        skew = report.timestamp - now
        if skew > self._max_future_skew:
            score -= 60.0
            reasons.append(
                f"Report timestamp is {skew} ahead of the current time, which is implausible"
            )

        age = now - report.timestamp
        if age > self._stale_report:
            score -= 20.0
            reasons.append(
                f"Report timestamp is {age} old, older than the {self._stale_report} freshness window"
            )

        if report.media and report.media.media_timestamp:
            media_age_gap = report.timestamp - report.media.media_timestamp
            if media_age_gap > self._media_stale:
                score -= 25.0
                reasons.append(
                    f"Attached media appears to be captured {media_age_gap} before the report "
                    "was filed; this lowers confidence without assuming the media is fake"
                )
            elif media_age_gap < -self._max_future_skew:
                score -= 15.0
                reasons.append("Attached media timestamp is after the report timestamp")

        if related_reports:
            close_in_time = [
                r
                for r in related_reports
                if abs(r.timestamp - report.timestamp) <= self._corroboration_window
            ]
            if related_reports and not close_in_time:
                score -= 15.0
                reasons.append(
                    "No related reports fall within the corroboration time window "
                    f"({self._corroboration_window})"
                )

        score = max(0.0, min(100.0, score))
        if not reasons:
            reasons.append("No timestamp inconsistencies detected")

        return TemporalConsistencyResult(score=round(score, 2), reasons=reasons)

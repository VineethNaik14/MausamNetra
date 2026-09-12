"""MODULE 1 — Source reliability.

Prototype scoring only. These values are NOT an official reliability
certification of any source category — they are a configurable starting
policy for an MVP decision-support tool.
"""
from __future__ import annotations

from typing import Dict, Mapping

from ..schemas.report import ReportSource

#: Default prototype reliability scores (0-100). Easy to override via
#: ``SourceReliabilityScorer(overrides={...})`` without touching this file.
DEFAULT_SOURCE_SCORES: Dict[ReportSource, float] = {
    ReportSource.WEATHER_API: 95.0,
    ReportSource.GOVERNMENT: 95.0,
    ReportSource.VERIFIED_NEWS: 80.0,
    ReportSource.CITIZEN: 55.0,
    ReportSource.SOCIAL_MEDIA: 35.0,
    ReportSource.UNKNOWN: 25.0,
}


class SourceReliabilityScorer:
    """Looks up a configurable reliability score for a report source."""

    def __init__(self, overrides: Mapping[ReportSource, float] | None = None) -> None:
        self._scores: Dict[ReportSource, float] = dict(DEFAULT_SOURCE_SCORES)
        if overrides:
            for source, score in overrides.items():
                if not (0.0 <= score <= 100.0):
                    raise ValueError(f"Reliability score for {source} must be within [0, 100]")
                self._scores[source] = score

    def get_source_reliability(self, source: ReportSource) -> float:
        """Return the configured reliability score (0-100) for a source."""
        return self._scores.get(source, self._scores[ReportSource.UNKNOWN])

    def explain(self, source: ReportSource) -> str:
        score = self.get_source_reliability(source)
        return f"Source '{source.value}' has a configured reliability score of {score:.0f}/100"

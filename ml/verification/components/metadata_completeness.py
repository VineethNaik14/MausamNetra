"""MODULE 8 — Metadata completeness.

Required fields are weighted heavily; optional fields contribute smaller
bonuses so legitimate minimal reports aren't punished excessively.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..schemas.report import NormalizedWeatherReport

# (field name, weight) — required fields sum to 80, optional to 20.
_REQUIRED_FIELDS: List[tuple[str, float]] = [
    ("report_id", 20.0),
    ("source", 15.0),
    ("timestamp", 15.0),
    ("text", 15.0),
    ("event_type", 15.0),
]
_OPTIONAL_FIELDS: List[tuple[str, float]] = [
    ("latitude", 5.0),
    ("longitude", 5.0),
    ("city", 4.0),
    ("state", 3.0),
    ("media", 3.0),
]


@dataclass(frozen=True)
class MetadataCompletenessResult:
    score: float  # 0-100
    missing_required: List[str]
    missing_optional: List[str]


class MetadataCompletenessScorer:
    """Scores how complete a report's metadata is, out of 100."""

    def score(self, report: NormalizedWeatherReport) -> MetadataCompletenessResult:
        total = 0.0
        missing_required: List[str] = []
        missing_optional: List[str] = []

        for field_name, weight in _REQUIRED_FIELDS:
            value = getattr(report, field_name, None)
            if _is_present(value):
                total += weight
            else:
                missing_required.append(field_name)

        for field_name, weight in _OPTIONAL_FIELDS:
            value = getattr(report, field_name, None)
            if _is_present(value):
                total += weight
            else:
                missing_optional.append(field_name)

        return MetadataCompletenessResult(
            score=round(min(100.0, total), 2),
            missing_required=missing_required,
            missing_optional=missing_optional,
        )


def _is_present(value) -> bool:
    if value is None:
        return False
    if value == "unknown":
        return False
    return True

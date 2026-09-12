from __future__ import annotations

from ml.verification.components.location_consistency import LocationConsistencyResult
from ml.verification.components.metadata_completeness import MetadataCompletenessResult
from ml.verification.components.suspicious_detector import SuspiciousReportDetector
from ml.verification.components.temporal_consistency import TemporalConsistencyResult


def test_multiple_red_flags_marks_suspicious():
    detector = SuspiciousReportDetector()
    result = detector.detect(
        source_reliability=10.0,
        location_result=LocationConsistencyResult(score=10.0, reason="GPS conflicts with reported location"),
        temporal_result=TemporalConsistencyResult(score=90.0, reasons=["No timestamp inconsistencies detected"]),
        cross_source_agreement=20.0,
        metadata_result=MetadataCompletenessResult(score=80.0, missing_required=[], missing_optional=[]),
        image_duplicate=None,
    )
    assert result.is_suspicious is True
    assert len(result.reasons) >= 2


def test_single_red_flag_not_enough_to_mark_suspicious():
    detector = SuspiciousReportDetector()
    result = detector.detect(
        source_reliability=90.0,
        location_result=LocationConsistencyResult(score=95.0, reason="ok"),
        temporal_result=TemporalConsistencyResult(score=95.0, reasons=["No timestamp inconsistencies detected"]),
        cross_source_agreement=10.0,  # only this one is bad
        metadata_result=MetadataCompletenessResult(score=90.0, missing_required=[], missing_optional=[]),
        image_duplicate=None,
    )
    assert result.is_suspicious is False
    assert len(result.reasons) == 1


def test_never_returns_bare_boolean_without_reasons():
    detector = SuspiciousReportDetector()
    result = detector.detect(
        source_reliability=90.0,
        location_result=LocationConsistencyResult(score=95.0, reason="ok"),
        temporal_result=TemporalConsistencyResult(score=95.0, reasons=["No timestamp inconsistencies detected"]),
        cross_source_agreement=90.0,
        metadata_result=MetadataCompletenessResult(score=90.0, missing_required=[], missing_optional=[]),
        image_duplicate=None,
    )
    assert result.is_suspicious is False
    assert isinstance(result.reasons, list)

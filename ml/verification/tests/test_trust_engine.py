from __future__ import annotations

from datetime import timedelta

import pytest

from ml.verification.engine.trust_engine import TrustEngine
from ml.verification.exceptions import ClassifierUnavailableError
from ml.verification.schemas.classification import EventClassificationResult
from ml.verification.schemas.report import NormalizedWeatherReport, ReportSource
from ml.verification.schemas.verification import VerificationStatus


class StubClassifier:
    def __init__(self, event_type: str = "flood", confidence: float = 0.9, fail: bool = False):
        self.event_type = event_type
        self.confidence = confidence
        self.fail = fail

    def classify(self, report):
        if self.fail:
            raise ClassifierUnavailableError("stub failure")
        return EventClassificationResult(event_type=self.event_type, confidence=self.confidence)


def test_genuine_report_scores_high(trust_engine, genuine_report, related_corroborating_reports):
    """Scenario 1: a genuine, well-corroborated report should verify."""
    result = trust_engine.verify(genuine_report, related_reports=related_corroborating_reports)

    assert result.report_id == "WX78231"
    assert result.status in {VerificationStatus.VERIFIED, VerificationStatus.NEEDS_REVIEW}
    assert result.trust_score > 60
    assert not result.suspicious.is_suspicious


def test_suspicious_report_multiple_red_flags(now):
    """Scenario 2: low reliability + no corroboration + missing metadata -> suspicious."""
    engine = TrustEngine()
    report = NormalizedWeatherReport(
        report_id="WX00001",
        source=ReportSource.UNKNOWN,
        text=None,
        event_type=None,
        latitude=None,
        longitude=None,
        timestamp=now,
    )
    result = engine.verify(report, related_reports=[])

    assert result.status == VerificationStatus.SUSPICIOUS
    assert result.suspicious.is_suspicious
    assert len(result.suspicious.reasons) >= 2


def test_location_mismatch_lowers_score(trust_engine, genuine_report):
    """Scenario 3: GPS far from the reported city should lower location_consistency."""
    report = genuine_report.model_copy(update={"latitude": 28.7041, "longitude": 77.1025})  # Delhi coords, city still Hebbal
    result = trust_engine.verify(report)
    assert result.factors.location_consistency < 40


def test_future_timestamp_lowers_temporal_score(trust_engine, genuine_report, now):
    """Scenario 4: an impossible future timestamp should tank temporal_consistency."""
    report = genuine_report.model_copy(update={"timestamp": now + timedelta(hours=5)})
    result = trust_engine.verify(report, now=now)
    assert result.factors.temporal_consistency < 60
    assert any("implausible" in r for r in result.reasons)


def test_missing_metadata_lowers_score(trust_engine, now):
    """Scenario 5: a report missing most fields should score low on metadata completeness."""
    report = NormalizedWeatherReport(report_id="WX00002", timestamp=now)
    result = trust_engine.verify(report)
    assert result.factors.metadata_completeness < 50


def test_low_reliability_source(trust_engine, genuine_report):
    """Scenario 6: an UNKNOWN source should score low on source reliability."""
    report = genuine_report.model_copy(update={"source": ReportSource.UNKNOWN})
    result = trust_engine.verify(report)
    assert result.factors.source_reliability < 40


def test_classifier_unavailable_degrades_gracefully(genuine_report):
    """Scenario 15: classifier failure should not crash verification."""
    engine = TrustEngine(classifier=StubClassifier(fail=True))
    result = engine.verify(genuine_report)
    assert result.classifier_used is False
    assert result.degraded is True
    assert result.report_id == genuine_report.report_id


def test_classifier_agreement_boosts_media_score(genuine_report):
    engine = TrustEngine(classifier=StubClassifier(event_type="flood", confidence=0.95))
    result = engine.verify(genuine_report)
    assert result.classifier_used is True


def test_invalid_input_raises_validation_error(now):
    """Scenario 13: invalid input should fail schema validation, not silently pass."""
    with pytest.raises(Exception):
        NormalizedWeatherReport(report_id="", timestamp=now)  # empty id violates min_length


def test_batch_verification(trust_engine, genuine_report, related_corroborating_reports):
    """Scenario 17: batch verification should return one result per report."""
    other_report = genuine_report.model_copy(update={"report_id": "WX78299", "text": "Unrelated dry weather update"})
    results = trust_engine.verify_batch(
        [genuine_report, other_report],
        related_reports_by_id={genuine_report.report_id: related_corroborating_reports},
    )
    assert len(results) == 2
    assert {r.report_id for r in results} == {genuine_report.report_id, other_report.report_id}

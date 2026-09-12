from __future__ import annotations

from datetime import timedelta

from ml.verification.components.temporal_consistency import TemporalConsistencyChecker
from ml.verification.schemas.report import MediaAsset


def test_normal_timestamp_scores_high(genuine_report, now):
    checker = TemporalConsistencyChecker()
    result = checker.check(genuine_report, now=now)
    assert result.score >= 80


def test_future_timestamp_flagged(genuine_report, now):
    checker = TemporalConsistencyChecker()
    report = genuine_report.model_copy(update={"timestamp": now + timedelta(hours=2)})
    result = checker.check(report, now=now)
    assert result.score < 60
    assert any("implausible" in r for r in result.reasons)


def test_stale_report_flagged(genuine_report, now):
    checker = TemporalConsistencyChecker(stale_report_hours=1)
    report = genuine_report.model_copy(update={"timestamp": now - timedelta(hours=10)})
    result = checker.check(report, now=now)
    assert result.score < 100
    assert any("old" in r for r in result.reasons)


def test_old_media_lowers_but_does_not_zero_score(genuine_report, now):
    checker = TemporalConsistencyChecker(media_stale_hours=1)
    report = genuine_report.model_copy(
        update={
            "timestamp": now,
            "media": MediaAsset(url="img.jpg", media_timestamp=now - timedelta(days=30)),
        }
    )
    result = checker.check(report, now=now)
    assert 0 < result.score < 100

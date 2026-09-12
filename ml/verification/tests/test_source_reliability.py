from __future__ import annotations

from ml.verification.components.source_reliability import SourceReliabilityScorer
from ml.verification.schemas.report import ReportSource


def test_known_sources_ranked_sensibly():
    scorer = SourceReliabilityScorer()
    assert scorer.get_source_reliability(ReportSource.GOVERNMENT) > scorer.get_source_reliability(
        ReportSource.CITIZEN
    )
    assert scorer.get_source_reliability(ReportSource.CITIZEN) > scorer.get_source_reliability(
        ReportSource.UNKNOWN
    )


def test_overrides_apply():
    scorer = SourceReliabilityScorer(overrides={ReportSource.CITIZEN: 10.0})
    assert scorer.get_source_reliability(ReportSource.CITIZEN) == 10.0


def test_invalid_override_rejected():
    import pytest

    with pytest.raises(ValueError):
        SourceReliabilityScorer(overrides={ReportSource.CITIZEN: 150.0})


def test_explain_mentions_source_name():
    scorer = SourceReliabilityScorer()
    text = scorer.explain(ReportSource.WEATHER_API)
    assert "weather_api" in text

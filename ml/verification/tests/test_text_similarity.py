from __future__ import annotations

from ml.verification.components.text_similarity import (
    CrossSourceAgreementScorer,
    DuplicateTextDetector,
    TfidfSimilarityEngine,
)
from ml.verification.schemas.report import RelatedReport, ReportSource


def test_duplicate_text_detected(genuine_report, now):
    engine = TfidfSimilarityEngine()
    detector = DuplicateTextDetector(engine, duplicate_threshold=0.6, related_threshold=0.3)
    near_duplicate = RelatedReport(
        report_id="DUP1",
        source=ReportSource.CITIZEN,
        text="Heavy rainfall has caused severe waterlogging near Hebbal",
        timestamp=now,
    )
    result = detector.classify_pair(genuine_report, near_duplicate)
    assert result.relation == "duplicate"
    assert result.similarity > 0.6


def test_similar_but_not_duplicate_text(genuine_report, now):
    engine = TfidfSimilarityEngine()
    detector = DuplicateTextDetector(engine, duplicate_threshold=0.95, related_threshold=0.1)
    related = RelatedReport(
        report_id="REL1",
        source=ReportSource.WEATHER_API,
        text="Waterlogging reported around Hebbal",
        timestamp=now,
    )
    result = detector.classify_pair(genuine_report, related)
    assert result.relation in {"related", "unrelated"}


def test_unrelated_text(genuine_report, now):
    engine = TfidfSimilarityEngine()
    detector = DuplicateTextDetector(engine)
    unrelated = RelatedReport(
        report_id="UNREL1",
        source=ReportSource.CITIZEN,
        text="Clear skies and pleasant weather in Chennai today",
        timestamp=now,
    )
    result = detector.classify_pair(genuine_report, unrelated)
    assert result.relation == "unrelated"


def test_cross_source_independent_corroboration_scores_high(genuine_report, related_corroborating_reports):
    engine = TfidfSimilarityEngine()
    engine.fit_corpus(
        [genuine_report.text] + [r.text for r in related_corroborating_reports if r.text]
    )
    scorer = CrossSourceAgreementScorer(engine, related_threshold=0.1)
    score, reason = scorer.calculate_cross_source_agreement(genuine_report, related_corroborating_reports)
    assert score >= 70


def test_same_source_repetition_not_treated_as_corroboration(genuine_report, now):
    engine = TfidfSimilarityEngine()
    same_source_reports = [
        RelatedReport(
            report_id="SAME1",
            source=genuine_report.source,
            text=genuine_report.text,
            timestamp=now,
        )
    ]
    engine.fit_corpus([genuine_report.text, same_source_reports[0].text])
    scorer = CrossSourceAgreementScorer(engine, related_threshold=0.1)
    score, reason = scorer.calculate_cross_source_agreement(genuine_report, same_source_reports)
    assert score < 70
    assert "independent" in reason.lower() or "same-source" in reason.lower()


def test_no_related_reports_is_neutral(genuine_report):
    engine = TfidfSimilarityEngine()
    scorer = CrossSourceAgreementScorer(engine)
    score, reason = scorer.calculate_cross_source_agreement(genuine_report, [])
    assert score == 50.0

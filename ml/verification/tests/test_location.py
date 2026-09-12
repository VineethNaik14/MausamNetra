from __future__ import annotations

from ml.verification.components.location_consistency import LocationConsistencyChecker, haversine_km


def test_haversine_zero_distance():
    assert haversine_km(13.0358, 77.5970, 13.0358, 77.5970) == 0.0


def test_gps_matches_reported_city(genuine_report):
    checker = LocationConsistencyChecker()
    result = checker.check(genuine_report)
    assert result.score >= 60


def test_gps_conflicts_with_reported_city(genuine_report):
    checker = LocationConsistencyChecker()
    far_report = genuine_report.model_copy(update={"latitude": 28.7041, "longitude": 77.1025})
    result = checker.check(far_report)
    assert result.score < 30


def test_missing_coordinates_neutral(genuine_report):
    checker = LocationConsistencyChecker()
    report = genuine_report.model_copy(update={"latitude": None, "longitude": None})
    result = checker.check(report)
    assert 0 <= result.score <= 100
    assert "No GPS" in result.reason


def test_unknown_place_falls_back_to_related_reports(genuine_report, related_corroborating_reports):
    checker = LocationConsistencyChecker()
    report = genuine_report.model_copy(update={"city": "Notarealplace123"})
    result = checker.check(report, related_reports=related_corroborating_reports)
    assert result.score >= 60  # GPS still close to related reports

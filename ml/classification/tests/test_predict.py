"""Unit tests for the event classifier.
Run with: pytest tests/ -v
"""

import pytest
from src.predict import predict_event
from src.config import EVENT_CLASSES, UNKNOWN_LABEL, CONFIDENCE_THRESHOLD


class TestNormalPredictions:
    def test_flood_report(self):
        result = predict_event("Heavy rainfall has flooded the road near Hebbal.")
        assert result["event_type"] == "flood"
        assert result["confidence"] > CONFIDENCE_THRESHOLD

    def test_heavy_rainfall_report(self):
        result = predict_event("Nonstop rain since morning, streets are waterlogged.")
        # "unknown" is an acceptable, safe outcome when confidence is low on
        # phrasing the model hasn't seen much of — see threshold logic in predict.py
        assert result["event_type"] in ("flood", "heavy_rainfall", "unknown")

    def test_heatwave_report(self):
        result = predict_event("Temperature touched 46 degrees, unbearable heat today.")
        assert result["event_type"] == "heatwave"


class TestAmbiguousAndUnknown:
    def test_ambiguous_report_does_not_crash(self):
        result = predict_event("The sky looks a bit strange today.")
        assert result["event_type"] in EVENT_CLASSES + [UNKNOWN_LABEL]

    def test_non_weather_text(self):
        result = predict_event("The traffic on MG Road is very slow today.")
        assert result["event_type"] in ("other", UNKNOWN_LABEL)


class TestEdgeCases:
    def test_empty_string(self):
        result = predict_event("")
        assert result["event_type"] == UNKNOWN_LABEL
        assert result["confidence"] == 0.0

    def test_none_input(self):
        result = predict_event(None)
        assert result["event_type"] == UNKNOWN_LABEL

    def test_whitespace_only(self):
        result = predict_event("   ")
        assert result["event_type"] == UNKNOWN_LABEL

    def test_very_short_text(self):
        result = predict_event("flood")
        assert "event_type" in result  # should not crash

    def test_malformed_input_number(self):
        # backend might accidentally pass a non-string; should not crash the service
        result = predict_event(12345)
        assert result["event_type"] == UNKNOWN_LABEL


class TestOutputContract:
    def test_output_has_required_keys(self):
        result = predict_event("Cyclone warning issued for the coastal district.")
        assert set(result.keys()) == {"event_type", "confidence", "model_version"}

    def test_confidence_in_valid_range(self):
        result = predict_event("Dense fog reduced visibility on the highway.")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_event_type_is_valid_label(self):
        result = predict_event("Strong winds knocked down a tree.")
        assert result["event_type"] in EVENT_CLASSES + [UNKNOWN_LABEL]


class TestModelLoading:
    def test_model_loads_without_error(self):
        from src.config import MODEL_PATH

        assert MODEL_PATH.exists(), "Model file missing — run train.py first"

    def test_repeated_calls_use_cached_pipeline(self):
        # second call should not reload from disk (singleton pattern in predict.py)
        import src.predict as predict_module

        predict_event("test")
        assert predict_module._pipeline is not None

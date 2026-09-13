import pytest

from ingestion.normalizer import normalize_record


def valid_raw():
    return {
        "source": "citizen",
        "source_type": "citizen_report",
        "text": "Heavy rain near Hebbal",
        "timestamp": "2026-09-12T08:30:00+00:00",
        "latitude": 13.0358,
        "longitude": 77.5970,
        "city": "Bengaluru",
        "state": "Karnataka",
    }


def test_normalize_valid_record():
    report = normalize_record(valid_raw())
    assert report.source == "citizen"
    assert report.city == "Bengaluru"
    assert report.event_type is None


@pytest.mark.parametrize("field,value", [
    ("latitude", 200),
    ("longitude", 300),
])
def test_invalid_coordinates(field, value):
    raw = valid_raw()
    raw[field] = value
    with pytest.raises(Exception):
        normalize_record(raw)


def test_empty_text_rejected():
    raw = valid_raw()
    raw["text"] = "   "
    with pytest.raises(Exception):
        normalize_record(raw)


def test_invalid_timestamp_rejected():
    raw = valid_raw()
    raw["timestamp"] = "not-a-timestamp"
    with pytest.raises(Exception):
        normalize_record(raw)

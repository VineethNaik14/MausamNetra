from ingestion.dedup import TTLSeenCache


def report():
    return {
        "source": "citizen",
        "text": "Heavy rain near Hebbal",
        "latitude": 13.0358,
        "longitude": 77.5970,
        "timestamp": "2026-09-12T10:00:00+00:00",
    }


def test_duplicate_detection():
    cache = TTLSeenCache(ttl_seconds=60)
    assert cache.is_duplicate(report()) is False
    assert cache.is_duplicate(report()) is True

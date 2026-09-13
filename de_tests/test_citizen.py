from ingestion.citizen_reports.ingestion import ingest_citizen_report


def test_citizen_report():
    result = ingest_citizen_report({
        "text": "Heavy rainfall has caused waterlogging",
        "timestamp": "2026-09-12T10:30:00+00:00",
        "latitude": 13.0358,
        "longitude": 77.5970,
        "city": "Bengaluru",
        "state": "Karnataka",
    })
    assert result["source"] == "citizen"

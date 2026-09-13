from ingestion.cleaner import clean_text, normalize_source


def test_clean_text():
    assert clean_text("  Heavy   rain\nnear road ") == "Heavy rain near road"


def test_source_normalization():
    assert normalize_source("Citizen Report") == "citizen"

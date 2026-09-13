from pathlib import Path

from ingestion.dataset.csv_ingestion import ingest_csv


def test_dataset_ingestion():
    path = Path(__file__).parents[1] / "data" / "sample" / "weather_reports.csv"
    valid, rejected = ingest_csv(path)
    assert len(valid) >= 8
    assert len(rejected) >= 2

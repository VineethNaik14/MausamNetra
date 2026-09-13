import csv
import json
from pathlib import Path

from ..normalizer import normalize_record


REQUIRED_COLUMNS = {"source", "text", "latitude", "longitude", "timestamp"}


def ingest_csv(path: str | Path) -> tuple[list[dict], list[dict]]:
    """Read CSV rows and separate valid records from rejected records."""
    path = Path(path)
    valid: list[dict] = []
    rejected: list[dict] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = {c.strip() for c in (reader.fieldnames or [])}
        missing = REQUIRED_COLUMNS - columns

        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")

        for row_number, row in enumerate(reader, start=2):
            try:
                report = normalize_record(row)
                valid.append(report.model_dump(mode="json"))
            except Exception as exc:
                rejected.append({
                    "row_number": row_number,
                    "raw_record": row,
                    "error": str(exc),
                })

    return valid, rejected


def write_jsonl(records: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

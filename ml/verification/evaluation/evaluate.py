"""Evaluation script for the verification engine.

This script does NOT ship any accuracy numbers — it is a tool. You must
supply a labeled dataset before any metric means anything.

Expected input: a JSON file containing a list of objects shaped like::

    {
      "report": { ...NormalizedWeatherReport fields... },
      "related_reports": [ ...RelatedReport fields... ],
      "ground_truth_suspicious": true,
      "ground_truth_duplicate": false
    }

Usage:
    python -m ml.verification.evaluation.evaluate --data path/to/labeled_reports.json

Outputs precision/recall/F1/accuracy and a confusion matrix for BOTH the
suspicious-report decision and the duplicate decision, computed
separately (they are different tasks).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

from sklearn.metrics import classification_report, confusion_matrix

from ..engine.trust_engine import TrustEngine
from ..schemas.report import NormalizedWeatherReport, RelatedReport


def _load_dataset(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _evaluate_task(name: str, y_true: List[bool], y_pred: List[bool]) -> None:
    if not y_true:
        print(f"\n[{name}] No labeled examples found — skipping.")
        return

    print(f"\n=== {name} ===")
    print(classification_report(y_true, y_pred, target_names=["negative", "positive"], zero_division=0))
    print("Confusion matrix (rows=ground truth, cols=predicted) [neg, pos]:")
    print(confusion_matrix(y_true, y_pred, labels=[False, True]))


def run_evaluation(data_path: Path) -> None:
    dataset = _load_dataset(data_path)
    engine = TrustEngine()

    suspicious_true: List[bool] = []
    suspicious_pred: List[bool] = []
    duplicate_true: List[bool] = []
    duplicate_pred: List[bool] = []

    for entry in dataset:
        report = NormalizedWeatherReport.model_validate(entry["report"])
        related = [RelatedReport.model_validate(r) for r in entry.get("related_reports", [])]

        result = engine.verify(report, related_reports=related)

        if "ground_truth_suspicious" in entry:
            suspicious_true.append(bool(entry["ground_truth_suspicious"]))
            suspicious_pred.append(result.suspicious.is_suspicious)

        if "ground_truth_duplicate" in entry:
            duplicate_true.append(bool(entry["ground_truth_duplicate"]))
            duplicate_pred.append(result.duplicate.is_duplicate)

    _evaluate_task("Suspicious-report detection", suspicious_true, suspicious_pred)
    _evaluate_task("Duplicate detection", duplicate_true, duplicate_pred)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help="Path to labeled dataset JSON file")
    args = parser.parse_args(argv)

    if not args.data.exists():
        print(f"Dataset not found: {args.data}", file=sys.stderr)
        return 1

    run_evaluation(args.data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

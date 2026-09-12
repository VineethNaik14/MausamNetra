"""Evaluate the trained model on the held-out test split."""

import json

import pandas as pd
import joblib
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
)

from config import MODEL_PATH, MODELS_DIR, MODEL_VERSION, EVENT_CLASSES
from preprocess import clean_text


def main():
    pipeline = joblib.load(MODEL_PATH)
    test_df = pd.read_csv(MODELS_DIR / f"test_split_{MODEL_VERSION}.csv")
    test_df["text"] = test_df["text"].apply(clean_text)

    X_test, y_test = test_df["text"], test_df["event_type"]
    preds = pipeline.predict(X_test)

    acc = accuracy_score(y_test, preds)
    macro_f1 = f1_score(y_test, preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, preds, average="weighted", zero_division=0)

    print(f"Test Accuracy:    {acc:.4f}")
    print(f"Test Macro F1:    {macro_f1:.4f}")
    print(f"Test Weighted F1: {weighted_f1:.4f}\n")

    report = classification_report(
        y_test, preds, labels=EVENT_CLASSES, zero_division=0, output_dict=True
    )
    print(classification_report(y_test, preds, labels=EVENT_CLASSES, zero_division=0))

    cm = confusion_matrix(y_test, preds, labels=EVENT_CLASSES)
    print("Confusion matrix (rows=true, cols=predicted):")
    print(pd.DataFrame(cm, index=EVENT_CLASSES, columns=EVENT_CLASSES))

    results = {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
    }
    out_path = MODELS_DIR / f"eval_results_{MODEL_VERSION}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nEvaluation results saved to {out_path}")


if __name__ == "__main__":
    main()

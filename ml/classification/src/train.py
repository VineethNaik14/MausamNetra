"""Train the event classifier and save a versioned model + metadata."""

import json
from datetime import datetime, timezone

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, f1_score
import joblib

from config import (
    PROCESSED_DATA_PATH,
    MODEL_PATH,
    METADATA_PATH,
    MODELS_DIR,
    EVENT_CLASSES,
    RANDOM_STATE,
    TEST_SIZE,
    VAL_SIZE,
    MODEL_VERSION,
)
from preprocess import clean_text


def load_data() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DATA_PATH)
    df = df.dropna(subset=["text", "event_type"])
    df["text"] = df["text"].apply(clean_text)
    df = df[df["text"].str.len() > 0]  # drop rows that became empty after cleaning
    unknown_labels = set(df["event_type"]) - set(EVENT_CLASSES)
    if unknown_labels:
        raise ValueError(
            f"CSV has labels not in config.EVENT_CLASSES: {unknown_labels}"
        )
    return df


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(
                        1,
                        2,
                    ),  # unigrams + bigrams capture phrases like "heavy rainfall"
                    min_df=2,  # ignore terms appearing in only 1 document (noise)
                    max_df=0.9,  # ignore near-universal terms
                    stop_words="english",
                    sublinear_tf=True,  # log-scale term frequency, standard TF-IDF improvement
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",  # compensates for any class imbalance in your CSV
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def main():
    df = load_data()
    print(f"Loaded {len(df)} rows across {df['event_type'].nunique()} classes.")

    X, y = df["text"], df["event_type"]

    # Split: train / val / test, stratified so every split has proportional class representation
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    val_ratio = VAL_SIZE / (1 - TEST_SIZE)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio, stratify=y_temp, random_state=RANDOM_STATE
    )

    print(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    # Validation performance (used to sanity-check + tune threshold in evaluate.py)
    val_preds = pipeline.predict(X_val)
    val_macro_f1 = f1_score(y_val, val_preds, average="macro")
    print(f"\nValidation macro F1: {val_macro_f1:.4f}")
    print(classification_report(y_val, val_preds, zero_division=0))

    # Save model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    # Save metadata (Section 14 — model versioning)
    metadata = {
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "classes": EVENT_CLASSES,
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
        "val_macro_f1": round(val_macro_f1, 4),
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {METADATA_PATH}")

    # Persist the test split so evaluate.py uses the exact same held-out set
    test_df = pd.DataFrame({"text": X_test, "event_type": y_test})
    test_df.to_csv(MODELS_DIR / f"test_split_{MODEL_VERSION}.csv", index=False)


if __name__ == "__main__":
    main()

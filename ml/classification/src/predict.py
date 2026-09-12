"""Inference module — this is what the backend team imports.

Usage:
    from predict import predict_event
    result = predict_event("Heavy rainfall has flooded the road near Hebbal.")
    # {'event_type': 'flood', 'confidence': 0.94, 'model_version': 'event-classifier-v1'}
"""

import joblib

from config import MODEL_PATH, MODEL_VERSION, CONFIDENCE_THRESHOLD, UNKNOWN_LABEL
from preprocess import clean_text

_pipeline = None  # lazy-loaded singleton, avoids reloading the model on every call


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = joblib.load(MODEL_PATH)
    return _pipeline


def predict_event(text: str) -> dict:
    """Classify a single report's text into a weather event type.

    Args:
        text: Raw report text (any casing, may contain URLs/typos).

    Returns:
        dict with keys: event_type (str), confidence (float, 0-1),
        model_version (str).
    """
    pipeline = _get_pipeline()

    cleaned = clean_text(text)
    if cleaned == "":
        return {
            "event_type": UNKNOWN_LABEL,
            "confidence": 0.0,
            "model_version": MODEL_VERSION,
        }

    proba = pipeline.predict_proba([cleaned])[0]
    classes = pipeline.classes_
    best_idx = proba.argmax()
    predicted_class = classes[best_idx]
    confidence = float(proba[best_idx])

    if confidence < CONFIDENCE_THRESHOLD:
        predicted_class = UNKNOWN_LABEL

    return {
        "event_type": predicted_class,
        "confidence": round(confidence, 4),
        "model_version": MODEL_VERSION,
    }


if __name__ == "__main__":
    samples = [
        "Heavy rainfall has flooded the road near Hebbal.",
        "The traffic on MG Road is very slow today.",
        "",
        "asdkjaskjd random gibberish text",
    ]
    for s in samples:
        print(s, "->", predict_event(s))

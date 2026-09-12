"""Minimal FastAPI wrapper around predict_event().
This can either be its own file the backend mounts, or the backend
copies this route into their existing app — either way, only predict.py
is a real dependency.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from src.predict import predict_event

app = FastAPI(title="MausamNetra Event Classification")


class ClassifyRequest(BaseModel):
    report_id: str = "unknown"
    text: str


class ClassifyResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    report_id: str
    event_type: str
    confidence: float
    model_version: str


@app.post("/api/classify", response_model=ClassifyResponse)
def classify(request: ClassifyRequest):
    result = predict_event(request.text)
    return ClassifyResponse(
        report_id=request.report_id,
        event_type=result["event_type"],
        confidence=result["confidence"],
        model_version=result["model_version"],
    )


# Alias for the verification module's ExternalEventClassifierAdapter, which
# posts to POST {base_url}/classify by default (see
# mausamnetra_verification/ml/verification/adapters/classifier_http.py and
# README section 11). Same handler, same contract — kept as a separate route
# rather than renaming /api/classify so the backend integration in Phase 3
# keeps working unchanged.
app.post("/classify", response_model=ClassifyResponse)(classify)


@app.get("/health")
def health():
    return {"status": "ok"}

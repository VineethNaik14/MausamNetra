from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ml.verification.api import dependencies, routes


@pytest.fixture
def client():
    dependencies.get_trust_engine.cache_clear()
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app)


def _sample_report_payload(now_iso: str) -> dict:
    return {
        "report_id": "WX78231",
        "source": "citizen",
        "text": "Heavy rainfall has caused severe waterlogging near Hebbal",
        "event_type": "flood",
        "event_confidence": 0.94,
        "latitude": 13.0358,
        "longitude": 77.5970,
        "city": "Hebbal",
        "state": "Karnataka",
        "timestamp": now_iso,
    }


def test_health_endpoint(client):
    response = client.get("/api/v1/verification/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_verify_endpoint_happy_path(client):
    payload = {"report": _sample_report_payload("2026-09-12T09:30:00Z"), "related_reports": []}
    response = client.post("/api/v1/verification/verify", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["report_id"] == "WX78231"
    assert 0 <= body["trust_score"] <= 100
    assert body["status"] in {"VERIFIED", "NEEDS_REVIEW", "SUSPICIOUS"}


def test_verify_endpoint_invalid_input_returns_422(client):
    bad_payload = {"report": {"report_id": "", "timestamp": "2026-09-12T09:30:00Z"}}
    response = client.post("/api/v1/verification/verify", json=bad_payload)
    assert response.status_code == 422
    # Ensure no raw stack trace leaks to the client
    assert "Traceback" not in response.text


def test_batch_endpoint(client):
    payload = {
        "reports": [
            _sample_report_payload("2026-09-12T09:30:00Z"),
            {**_sample_report_payload("2026-09-12T09:31:00Z"), "report_id": "WX78232"},
        ]
    }
    response = client.post("/api/v1/verification/batch", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2


def test_batch_endpoint_rejects_oversized_batch(client):
    reports = [
        {**_sample_report_payload("2026-09-12T09:30:00Z"), "report_id": f"WX{i}"} for i in range(201)
    ]
    response = client.post("/api/v1/verification/batch", json={"reports": reports})
    assert response.status_code == 413


def test_similarity_endpoint(client):
    payload = {"text_a": "Flooded roads near Hebbal", "text_b": "Waterlogging reported in Hebbal"}
    response = client.post("/api/v1/verification/similarity", json=payload)
    assert response.status_code == 200
    assert "similarity" in response.json()

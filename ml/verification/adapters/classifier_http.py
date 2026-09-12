"""Adapter for a teammate's classifier exposed as a separate HTTP/FastAPI service.

Usage::

    from ml.verification.adapters.classifier_http import ExternalEventClassifierAdapter

    adapter = ExternalEventClassifierAdapter(
        base_url="http://classifier-service:8001",
        timeout_seconds=3.0,
    )
    result = adapter.classify(report)

Expected remote contract — ``POST {base_url}/classify``::

    Request:  {"text": "...", "report_id": "..."}
    Response: {"event_type": "flood", "confidence": 0.94}
"""
from __future__ import annotations

from typing import Optional

import requests

from ..exceptions import ClassifierTimeoutError, ClassifierUnavailableError
from ..logging_config import get_logger
from ..schemas.classification import EventClassificationResult
from ..schemas.report import NormalizedWeatherReport

logger = get_logger("adapters.classifier_http")


class ExternalEventClassifierAdapter:
    """Calls a remote classification microservice over HTTP."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 3.0,
        endpoint: str = "/classify",
        session: Optional[requests.Session] = None,
    ) -> None:
        self._url = base_url.rstrip("/") + endpoint
        self._timeout = timeout_seconds
        self._session = session or requests.Session()

    def classify(self, report: NormalizedWeatherReport) -> EventClassificationResult:
        payload = {"report_id": report.report_id, "text": report.text or ""}
        try:
            response = self._session.post(self._url, json=payload, timeout=self._timeout)
        except requests.Timeout as exc:
            logger.warning("Classifier HTTP timeout for report_id=%s", report.report_id)
            raise ClassifierTimeoutError(f"Classifier request timed out after {self._timeout}s") from exc
        except requests.RequestException as exc:
            logger.warning("Classifier HTTP error for report_id=%s: %s", report.report_id, exc)
            raise ClassifierUnavailableError("Could not reach the classification service") from exc

        if response.status_code != 200:
            raise ClassifierUnavailableError(
                f"Classification service returned HTTP {response.status_code}"
            )

        try:
            data = response.json()
            return EventClassificationResult(
                event_type=data["event_type"],
                confidence=float(data["confidence"]),
                model_version=data.get("model_version"),
            )
        except (ValueError, KeyError, TypeError) as exc:
            raise ClassifierUnavailableError("Classification service returned an unexpected payload") from exc

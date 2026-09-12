"""Adapter for a teammate's classifier that lives in-process as a Python object.

Usage (teammate's side)::

    from ml.verification.adapters.classifier_local import LocalEventClassifierAdapter
    from ml.verification.schemas.classification import EventClassificationResult

    class MyClassifier:
        def predict(self, text: str) -> tuple[str, float]:
            ...  # their model
            return "flood", 0.94

    adapter = LocalEventClassifierAdapter(MyClassifier())
    result = adapter.classify(report)  # -> EventClassificationResult
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from ..exceptions import ClassifierUnavailableError
from ..logging_config import get_logger
from ..schemas.classification import EventClassificationResult
from ..schemas.report import NormalizedWeatherReport

logger = get_logger("adapters.classifier_local")


class LocalEventClassifierAdapter:
    """Wraps an in-process model object to satisfy ``EventClassifierProtocol``.

    The wrapped model is not required to know anything about
    ``NormalizedWeatherReport`` or ``EventClassificationResult`` — supply
    a small ``predict_fn`` that adapts its native call signature.
    """

    def __init__(
        self,
        model: Any,
        predict_fn: Optional[Callable[[Any, NormalizedWeatherReport], tuple[str, float]]] = None,
        model_version: Optional[str] = None,
    ) -> None:
        self._model = model
        self._predict_fn = predict_fn or self._default_predict_fn
        self._model_version = model_version

    @staticmethod
    def _default_predict_fn(model: Any, report: NormalizedWeatherReport) -> tuple[str, float]:
        """Default assumes the model exposes ``.predict(text) -> (label, confidence)``."""
        return model.predict(report.text or "")

    def classify(self, report: NormalizedWeatherReport) -> EventClassificationResult:
        try:
            event_type, confidence = self._predict_fn(self._model, report)
        except Exception as exc:
            logger.warning("Local classifier failed for report_id=%s: %s", report.report_id, exc)
            raise ClassifierUnavailableError("Local event classifier raised an error") from exc

        return EventClassificationResult(
            event_type=event_type,
            confidence=float(confidence),
            model_version=self._model_version,
        )

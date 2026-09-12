"""The integration boundary between verification and event classification.

Your teammate's classification model — regardless of whether it is a
logistic regression, an SVM, a transformer, or a separate FastAPI
service — must be wrapped so it satisfies ``EventClassifierProtocol``.
The TrustEngine only ever calls ``classify()``.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..schemas.classification import EventClassificationResult
from ..schemas.report import NormalizedWeatherReport


@runtime_checkable
class EventClassifierProtocol(Protocol):
    """Structural interface for any event classifier implementation.

    Any object with a compatible ``classify`` method satisfies this
    protocol — no inheritance required (duck typing, checked
    structurally at runtime via ``isinstance(obj, EventClassifierProtocol)``).
    """

    def classify(self, report: NormalizedWeatherReport) -> EventClassificationResult:
        """Classify a report's weather-event type.

        Implementations MUST raise
        ``ml.verification.exceptions.ClassifierUnavailableError`` (or a
        subclass) on failure rather than returning a fabricated result,
        so the TrustEngine can degrade gracefully and explain why.
        """
        ...

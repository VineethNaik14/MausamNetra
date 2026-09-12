"""FastAPI dependency-injection wiring.

Models/engines are built once at import time (module-level singletons)
so Sentence Transformer/TF-IDF vectorizers are never reloaded per
request. Swap ``get_classifier()`` to plug in the teammate's real model
without touching any route code.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from ..config import get_settings
from ..engine.trust_engine import TrustEngine
from ..interfaces.classifier import EventClassifierProtocol
from ..interfaces.repositories import VerificationRepository
from ..logging_config import get_logger
from ..services.verification_service import VerificationService

logger = get_logger("api.dependencies")


@lru_cache(maxsize=1)
def get_trust_engine() -> TrustEngine:
    """Build (once) and return the shared TrustEngine instance."""
    settings = get_settings()
    classifier = _build_classifier()
    return TrustEngine(settings=settings, classifier=classifier)


def _build_classifier() -> Optional[EventClassifierProtocol]:
    """Wire up the configured classifier adapter, or None if unset.

    CLASSIFIER_MODE=http (recommended for the hackathon — the ML teammate's
    classifier runs as its own FastAPI service, see ml/classification/api/main.py)
    or CLASSIFIER_MODE=local (in-process import, no network hop — see
    _build_local_classifier below for the required repo layout).
    """
    settings = get_settings()
    if settings.classifier_mode == "http" and settings.classifier_http_url:
        from ..adapters.classifier_http import ExternalEventClassifierAdapter

        return ExternalEventClassifierAdapter(
            base_url=settings.classifier_http_url,
            timeout_seconds=settings.classifier_http_timeout_seconds,
        )
    if settings.classifier_mode == "local":
        return _build_local_classifier()
    # No local model wired by default — the TrustEngine works fine
    # without one (media/text consistency simply skips agreement checks).
    return None


def _build_local_classifier() -> Optional[EventClassifierProtocol]:
    """Wires the ML teammate's TF-IDF + Logistic Regression classifier
    in-process (no HTTP hop). Only used when CLASSIFIER_MODE=local.

    Assumes the standard MausamNetra monorepo layout, where both ML
    modules live under a shared ml/ folder:

        MausamNetra/
        ├── ml/
        │   ├── classification/
        │   │   └── src/predict.py, config.py   <- ML teammate's module
        │   └── verification/
        │       └── api/dependencies.py          (this file)
        └── main.py

    If your layout differs, adjust CLASSIFICATION_SRC below rather than
    restructuring either module.
    """
    import sys
    from pathlib import Path

    classification_src = (
        Path(__file__).resolve().parents[3] / "ml" / "classification" / "src"
    )
    if not classification_src.exists():
        logger.warning(
            "CLASSIFIER_MODE=local but %s was not found; classifier stays "
            "unwired and verification proceeds in degraded mode. Fix the "
            "path in _build_local_classifier(), or set CLASSIFIER_MODE=http "
            "and CLASSIFIER_HTTP_URL to point at the classifier's FastAPI "
            "service instead.",
            classification_src,
        )
        return None

    if str(classification_src) not in sys.path:
        sys.path.insert(0, str(classification_src))

    from config import MODEL_VERSION  # type: ignore[import-not-found]
    from predict import predict_event  # type: ignore[import-not-found]

    from ..adapters.classifier_local import LocalEventClassifierAdapter

    def _predict_fn(_model, report) -> tuple[str, float]:
        result = predict_event(report.text or "")
        return result["event_type"], result["confidence"]

    return LocalEventClassifierAdapter(
        model=predict_event,  # unused by our custom predict_fn; kept for API shape
        predict_fn=_predict_fn,
        model_version=MODEL_VERSION,
    )


_repository_singleton: Optional[VerificationRepository] = None


def set_repository(repository: Optional[VerificationRepository]) -> None:
    """Allow the backend app to inject its real SQLAlchemy-backed repository."""
    global _repository_singleton
    _repository_singleton = repository


def get_verification_service() -> VerificationService:
    engine = get_trust_engine()
    return VerificationService(engine=engine, repository=_repository_singleton)

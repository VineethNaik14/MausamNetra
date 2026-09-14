"""Real Event Classifier — HTTP adapter to the classification service
(ml/classification/api/main.py, POST /classify, default port 8000)."""
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.ai_integration import ClassifierInput, ClassifierOutput

logger = get_logger(__name__)


class RealEventClassifier:
    """Drop-in replacement for MockEventClassifier (same Protocol)."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.CLASSIFIER_SERVICE_URL).rstrip("/")
        self.timeout = timeout

    def classify(self, data: ClassifierInput) -> ClassifierOutput:
        payload = {"report_id": str(data.report_id), "text": data.text}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/classify", json=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            logger.error("classifier_service_error report_id=%s error=%s", data.report_id, exc)
            return ClassifierOutput(event_type="UNKNOWN", confidence=0.0)

        # their model returns lowercase labels ("flood"); backend contract is uppercase
        return ClassifierOutput(event_type=body["event_type"].upper(), confidence=body["confidence"])
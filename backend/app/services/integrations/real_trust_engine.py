"""Real Trust Engine — HTTP adapter to the verification service
(ml/verification/api/routes.py, POST /api/v1/verification/verify, port 8001)."""
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.ai_integration import TrustEngineInput, TrustEngineOutput

logger = get_logger(__name__)

_SOURCE_MAP = {
    "citizen": "citizen",
    "weather_api": "weather_api",
    "government": "government",
    "news": "verified_news",
    "public_feed": "social_media",
    "simulated_social": "social_media",
}


class RealTrustEngine:
    """Drop-in replacement for MockTrustEngine (same Protocol)."""

    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.VERIFICATION_SERVICE_URL).rstrip("/")
        self.timeout = timeout

    def evaluate(self, data: TrustEngineInput) -> TrustEngineOutput:
        raw_source = data.source_type or ""
        report_payload = {
            "report_id": str(data.report_id),
            "source": _SOURCE_MAP.get(raw_source, "unknown"),
            "text": data.text,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "timestamp": data.timestamp,
            "media": None,
        }
        related_payload = [
            {"report_id": str(c.report_id), "timestamp": data.timestamp}
            for c in data.corroborating_reports
        ]
        payload = {"report": report_payload, "related_reports": related_payload}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/v1/verification/verify", json=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            logger.error("verification_service_error report_id=%s error=%s", data.report_id, exc)
            return TrustEngineOutput(
                trust_score=0, status="NEEDS_REVIEW",
                reasons=["Verification service unavailable — flagged for manual review"],
            )

        return TrustEngineOutput(
            trust_score=int(round(body["trust_score"])),
            status=body["status"],
            reasons=body.get("reasons", []),
        )
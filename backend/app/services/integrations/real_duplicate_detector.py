"""Real Duplicate Detector — uses the verification service's
text-similarity engine (POST /api/v1/verification/similarity) to compare
the current report against each candidate."""
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.ai_integration import DuplicateDetectorInput, DuplicateDetectorOutput

logger = get_logger(__name__)

# Matches TEXT_SIMILARITY_THRESHOLD's default in ml/verification/config.py
SIMILARITY_THRESHOLD = 0.85


class RealDuplicateDetector:
    """Drop-in replacement for MockDuplicateDetector (same Protocol)."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.VERIFICATION_SERVICE_URL).rstrip("/")
        self.timeout = timeout

    def detect(self, data: DuplicateDetectorInput) -> DuplicateDetectorOutput:
        current_text = data.current_report.text or ""
        if not current_text.strip() or not data.candidate_reports:
            return DuplicateDetectorOutput(is_duplicate=False, similarity_score=0.0)

        best_score = 0.0
        best_match_id = None

        try:
            with httpx.Client(timeout=self.timeout) as client:
                for candidate in data.candidate_reports:
                    if not candidate.text:
                        continue
                    resp = client.post(
                        f"{self.base_url}/api/v1/verification/similarity",
                        json={"text_a": current_text, "text_b": candidate.text},
                    )
                    resp.raise_for_status()
                    score = resp.json()["similarity"]
                    if score > best_score:
                        best_score = score
                        best_match_id = candidate.report_id
        except httpx.HTTPError as exc:
            logger.error(
                "duplicate_detector_service_error report_id=%s error=%s",
                data.current_report.report_id, exc,
            )
            return DuplicateDetectorOutput(is_duplicate=False, similarity_score=0.0)

        is_duplicate = best_score >= SIMILARITY_THRESHOLD and best_match_id is not None
        return DuplicateDetectorOutput(
            is_duplicate=is_duplicate,
            master_report_id=best_match_id if is_duplicate else None,
            similarity_score=round(best_score, 4),
        )
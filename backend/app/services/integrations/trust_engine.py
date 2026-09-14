"""
Trust Engine integration boundary.

============================================================================
INTEGRATION POINT FOR: Trust / Verification Team
============================================================================
Replace `MockTrustEngine` with a real implementation of the `TrustEngine`
Protocol and wire it up in app/dependencies/services.py (get_trust_engine).

Contract:
    INPUT  -> app.schemas.ai_integration.TrustEngineInput
    OUTPUT -> app.schemas.ai_integration.TrustEngineOutput

Example OUTPUT:
    {
      "trust_score": 91,
      "status": "VERIFIED",
      "reasons": ["Strong location consistency", "Multiple corroborating reports"]
    }

IMPORTANT: The mock below implements a simple, transparent heuristic. It
MUST NOT be presented to users/judges as a real AI verification system -
it exists only so report -> verification -> incident flow works end-to-end
during development.
============================================================================
"""
from typing import Protocol

from app.core.logging import get_logger
from app.schemas.ai_integration import TrustEngineInput, TrustEngineOutput

logger = get_logger(__name__)


def score_to_status(score: int) -> str:
    """Prototype policy - NOT an official IMD threshold."""
    if score >= 80:
        return "VERIFIED"
    if score >= 60:
        return "NEEDS_REVIEW"
    return "SUSPICIOUS"


class TrustEngine(Protocol):
    def evaluate(self, data: TrustEngineInput) -> TrustEngineOutput:
        ...


class MockTrustEngine:
    """
    Simple, explainable heuristic trust engine for prototype/demo purposes.

    Score components (each contributes points, capped at 100):
    - base score from source reliability (0-40)
    - +15 for each corroborating report, up to +30
    - +15 if media is attached
    - +15 if the report text is reasonably descriptive (length-based heuristic)
    """

    def evaluate(self, data: TrustEngineInput) -> TrustEngineOutput:
        reasons: list[str] = []

        score = int(min(40, max(0, data.source_reliability * 0.4)))
        reasons.append(f"Base score from source reliability ({data.source_reliability:.0f}/100)")

        corroboration_bonus = min(30, len(data.corroborating_reports) * 15)
        if corroboration_bonus:
            reasons.append(f"{len(data.corroborating_reports)} corroborating report(s) nearby")
        score += corroboration_bonus

        if data.has_media:
            score += 15
            reasons.append("Report includes supporting media")

        if len(data.text.strip()) >= 40:
            score += 15
            reasons.append("Report text is reasonably descriptive")

        score = max(0, min(100, score))
        status = score_to_status(score)

        logger.info("MockTrustEngine scored report %s -> %s (%s)", data.report_id, score, status)
        return TrustEngineOutput(trust_score=score, status=status, reasons=reasons)


# TODO(trust-team): Implement RealTrustEngine(TrustEngine) here or in a
# separate module, then update app/dependencies/services.py::get_trust_engine
# to return it instead of MockTrustEngine.

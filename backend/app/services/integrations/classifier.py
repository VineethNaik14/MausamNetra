"""
Event Classifier integration boundary.

============================================================================
INTEGRATION POINT FOR: Event Classification Team
============================================================================
Replace `MockEventClassifier` with a real implementation (e.g.
`RealEventClassifier`) that implements the same `EventClassifier` Protocol.
Wire it up in app/dependencies/services.py (get_event_classifier) - no
changes to routes, services, or the database layer are required.

Contract:
    INPUT  -> app.schemas.ai_integration.ClassifierInput
    OUTPUT -> app.schemas.ai_integration.ClassifierOutput

Example:
    INPUT:  {"report_id": "...", "text": "Heavy rainfall has flooded roads"}
    OUTPUT: {"event_type": "FLOOD", "confidence": 0.94}

Suggested real implementation approach (not built here on purpose):
    - Fine-tuned text classifier (scikit-learn / transformers) over
      keywords + embeddings for event_type in {FLOOD, HEATWAVE, STORM,
      CYCLONE, LIGHTNING, LANDSLIDE, ...}
    - Optionally combine with image analysis (OpenCV / vision model) when
      media_url is present.
============================================================================
"""
from typing import Protocol

from app.core.logging import get_logger
from app.schemas.ai_integration import ClassifierInput, ClassifierOutput

logger = get_logger(__name__)

# Keep this list loosely aligned with whatever the real classifier team
# settles on; it's only used by the mock for a plausible-looking demo.
_KNOWN_EVENT_KEYWORDS: dict[str, list[str]] = {
    "FLOOD": ["flood", "waterlog", "inundat", "overflow", "submerg"],
    "HEATWAVE": ["heatwave", "heat wave", "scorching", "extreme heat"],
    "STORM": ["storm", "thunderstorm", "gale", "squall"],
    "CYCLONE": ["cyclone", "hurricane", "typhoon"],
    "LIGHTNING": ["lightning", "thunder", "strike"],
    "LANDSLIDE": ["landslide", "mudslide", "rockfall"],
    "HAIL": ["hail", "hailstorm"],
    "DROUGHT": ["drought", "dry spell"],
}


class EventClassifier(Protocol):
    """Interface every event classifier implementation must satisfy."""

    def classify(self, data: ClassifierInput) -> ClassifierOutput:
        ...


class MockEventClassifier:
    """
    Deterministic, keyword-based mock classifier for local development and
    demos. This is NOT a real AI model - it exists purely so the rest of
    the pipeline (trust, duplicates, correlation, WebSocket, dashboard) can
    be built and tested end-to-end before the real classifier is ready.
    """

    def classify(self, data: ClassifierInput) -> ClassifierOutput:
        text_lower = data.text.lower()
        for event_type, keywords in _KNOWN_EVENT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                logger.info("MockEventClassifier matched event_type=%s", event_type)
                return ClassifierOutput(event_type=event_type, confidence=0.75)

        logger.info("MockEventClassifier found no keyword match; returning UNKNOWN")
        return ClassifierOutput(event_type="UNKNOWN", confidence=0.3)


# TODO(ai-team): Implement RealEventClassifier(EventClassifier) here or in a
# separate module, then update app/dependencies/services.py::get_event_classifier
# to return it instead of MockEventClassifier.

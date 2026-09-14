"""
Duplicate Detector integration boundary.

============================================================================
INTEGRATION POINT FOR: Duplicate Detection Team
============================================================================
Replace `MockDuplicateDetector` with a real implementation (e.g. using
Sentence Transformers cosine similarity over report text, and/or perceptual
hashing / image embeddings over media_url with OpenCV) that implements the
`DuplicateDetector` Protocol. Wire it up in
app/dependencies/services.py::get_duplicate_detector.

Contract:
    INPUT  -> app.schemas.ai_integration.DuplicateDetectorInput
    OUTPUT -> app.schemas.ai_integration.DuplicateDetectorOutput

Example OUTPUT:
    {"is_duplicate": true, "master_report_id": "...", "similarity_score": 0.93}
============================================================================
"""
import difflib
from typing import Protocol

from app.core.logging import get_logger
from app.schemas.ai_integration import DuplicateDetectorInput, DuplicateDetectorOutput

logger = get_logger(__name__)

SIMILARITY_THRESHOLD = 0.85


class DuplicateDetector(Protocol):
    def detect(self, data: DuplicateDetectorInput) -> DuplicateDetectorOutput:
        ...


class MockDuplicateDetector:
    """
    Naive text-similarity mock using difflib's SequenceMatcher (no ML
    dependency required). This is NOT semantic similarity - it is a
    placeholder so the duplicate pipeline (storage, API, incident counters)
    can be exercised end-to-end before the real embedding-based detector
    is integrated.
    """

    def detect(self, data: DuplicateDetectorInput) -> DuplicateDetectorOutput:
        current_text = data.current_report.text.lower()
        best_score = 0.0
        best_match_id = None

        for candidate in data.candidate_reports:
            ratio = difflib.SequenceMatcher(None, current_text, candidate.text.lower()).ratio()
            if ratio > best_score:
                best_score = ratio
                best_match_id = candidate.report_id

        is_duplicate = best_score >= SIMILARITY_THRESHOLD and best_match_id is not None
        if is_duplicate:
            logger.info(
                "MockDuplicateDetector: report %s flagged as duplicate of %s (score=%.2f)",
                data.current_report.report_id,
                best_match_id,
                best_score,
            )

        return DuplicateDetectorOutput(
            is_duplicate=is_duplicate,
            master_report_id=best_match_id if is_duplicate else None,
            similarity_score=round(best_score, 4),
        )


# TODO(dup-detection-team): Implement RealDuplicateDetector(DuplicateDetector)
# here or in a separate module, then update
# app/dependencies/services.py::get_duplicate_detector to return it instead
# of MockDuplicateDetector.

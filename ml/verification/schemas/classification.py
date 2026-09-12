"""Contract shared with the teammate's event-classification model.

The TrustEngine depends ONLY on ``EventClassificationResult``. It never
imports the teammate's model code directly — see
``interfaces/classifier.py`` for the abstraction boundary.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EventClassificationResult(BaseModel):
    """Output contract the classifier must produce.

    Example:
        EventClassificationResult(event_type="flood", confidence=0.94)
    """

    model_config = ConfigDict(protected_namespaces=())

    event_type: str = Field(..., min_length=1, max_length=64)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: Optional[str] = Field(
        default=None,
        description="Optional identifier for which model produced this result.",
    )

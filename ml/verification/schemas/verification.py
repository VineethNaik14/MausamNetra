"""Outbound schemas produced by the verification engine."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SUSPICIOUS = "SUSPICIOUS"


class TrustFactors(BaseModel):
    """The individual 0-100 factor scores that make up the trust score."""

    source_reliability: float = Field(..., ge=0, le=100)
    location_consistency: float = Field(..., ge=0, le=100)
    temporal_consistency: float = Field(..., ge=0, le=100)
    cross_source_agreement: float = Field(..., ge=0, le=100)
    media_text_consistency: float = Field(..., ge=0, le=100)
    metadata_completeness: float = Field(..., ge=0, le=100)


class DuplicateInfo(BaseModel):
    """Result of duplicate detection against text and/or image similarity."""

    is_duplicate: bool = False
    is_related: bool = False
    master_report_id: Optional[str] = None
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: Optional[str] = None


class SuspiciousReportResult(BaseModel):
    """Explainable suspicious-report determination."""

    is_suspicious: bool
    reasons: List[str] = Field(default_factory=list)


class ImageDuplicateResult(BaseModel):
    """Result of the image perceptual-hash comparison."""

    possible_duplicate: bool
    similarity: float = Field(..., ge=0.0, le=1.0)
    reason: str


class VerificationResult(BaseModel):
    """The central, structured output of ``TrustEngine.verify()``.

    This is the single contract the backend persists into the
    ``Verification`` and ``Duplicate`` tables.
    """

    report_id: str
    trust_score: float = Field(..., ge=0, le=100)
    status: VerificationStatus

    factors: TrustFactors
    reasons: List[str] = Field(default_factory=list)

    duplicate: DuplicateInfo = Field(default_factory=DuplicateInfo)
    suspicious: SuspiciousReportResult = Field(
        default_factory=lambda: SuspiciousReportResult(is_suspicious=False, reasons=[])
    )

    classifier_used: bool = Field(
        default=True, description="False if classification was unavailable/degraded."
    )
    degraded: bool = Field(
        default=False, description="True if any dependency failed and defaults were used."
    )

    class Config:
        use_enum_values = True


class BatchVerificationResult(BaseModel):
    """Result wrapper for ``/api/v1/verification/batch``."""

    results: List[VerificationResult]
    failed_report_ids: List[str] = Field(default_factory=list)

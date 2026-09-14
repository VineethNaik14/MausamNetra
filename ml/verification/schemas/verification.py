"""Verification result schemas.

RECONSTRUCTED FILE — the original ``ml/verification/schemas/verification.py``
was missing from the delivered zip (it contained a duplicate copy of the
standalone ASGI app instead of these class definitions), which made the
verification service fail to start with an ImportError.

Every class/field below was reverse-engineered from how the rest of the
``ml/verification`` package actually constructs and reads these objects
(engine/trust_engine.py, components/image_similarity.py,
components/suspicious_detector.py, services/verification_service.py,
interfaces/repositories.py, api/routes.py, and the test suite), so the
shapes match the existing code exactly — nothing else in the package
needs to change.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Final verdict for a report. Compared by value against the
    ``VERIFIED_THRESHOLD`` / ``REVIEW_THRESHOLD`` settings in config.py.
    """

    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SUSPICIOUS = "SUSPICIOUS"
    REJECTED = "REJECTED"  # not currently produced by TrustEngine._decide_status,
    # kept for parity with the backend's VerificationStatus enum


class TrustFactors(BaseModel):
    """The six weighted components that make up the overall trust_score.

    Field names match app.schemas.ai_integration on the backend side 1:1.
    """

    source_reliability: float = Field(ge=0, le=100)
    location_consistency: float = Field(ge=0, le=100)
    temporal_consistency: float = Field(ge=0, le=100)
    cross_source_agreement: float = Field(ge=0, le=100)
    media_text_consistency: float = Field(ge=0, le=100)
    metadata_completeness: float = Field(ge=0, le=100)


class DuplicateInfo(BaseModel):
    """Result of text-based duplicate/related-report detection."""

    is_duplicate: bool = False
    is_related: bool = False
    master_report_id: Optional[str] = None
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: Optional[str] = None


class ImageDuplicateResult(BaseModel):
    """Result of perceptual-hash based image duplicate detection."""

    possible_duplicate: bool = False
    matched_report_id: Optional[str] = None
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""


class SuspiciousReportResult(BaseModel):
    """Aggregated suspicious/not-suspicious verdict with explanations."""

    is_suspicious: bool = False
    reasons: List[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    """Full output of TrustEngine.verify() for a single report.

    This is the response_model for POST /api/v1/verification/verify.
    """

    report_id: str
    trust_score: float = Field(ge=0, le=100)
    status: VerificationStatus
    factors: TrustFactors
    reasons: List[str] = Field(default_factory=list)
    duplicate: DuplicateInfo
    suspicious: SuspiciousReportResult
    classifier_used: bool = False
    degraded: bool = False


class BatchVerificationResult(BaseModel):
    """Response for POST /api/v1/verification/batch."""

    results: List[VerificationResult] = Field(default_factory=list)
    failed_report_ids: List[str] = Field(default_factory=list)
"""
Pydantic contracts shared between the core backend and the AI/ML teammates'
modules (event classification, trust engine, duplicate detection).

These schemas are the STABLE INTERFACE. The AI team should treat the
Input/Output shapes here as a contract: as long as their real implementation
consumes/produces these shapes, they can swap in for the Mock* classes in
app/services/integrations/ without any change to routes or the database
layer.
"""
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Event Classifier
# ---------------------------------------------------------------------------
class ClassifierInput(BaseModel):
    report_id: uuid.UUID
    text: str
    media_url: Optional[str] = None


class ClassifierOutput(BaseModel):
    event_type: str
    confidence: float = Field(ge=0, le=1)


# ---------------------------------------------------------------------------
# Trust Engine
# ---------------------------------------------------------------------------
class CorroboratingReport(BaseModel):
    report_id: uuid.UUID
    distance_km: Optional[float] = None
    time_delta_minutes: Optional[float] = None


class TrustEngineInput(BaseModel):
    report_id: uuid.UUID
    text: str
    source_reliability: float
    source_type: Optional[str] = None
    latitude: float
    longitude: float
    timestamp: str
    metadata: Optional[dict[str, Any]] = None
    corroborating_reports: list[CorroboratingReport] = Field(default_factory=list)
    has_media: bool = False


class TrustEngineOutput(BaseModel):
    trust_score: int = Field(ge=0, le=100)
    status: str  # VERIFIED | NEEDS_REVIEW | SUSPICIOUS | REJECTED
    reasons: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Duplicate Detector
# ---------------------------------------------------------------------------
class CandidateReport(BaseModel):
    report_id: uuid.UUID
    text: str
    media_url: Optional[str] = None
    latitude: float
    longitude: float
    timestamp: str


class DuplicateDetectorInput(BaseModel):
    current_report: CandidateReport
    candidate_reports: list[CandidateReport] = Field(default_factory=list)


class DuplicateDetectorOutput(BaseModel):
    is_duplicate: bool
    master_report_id: Optional[uuid.UUID] = None
    similarity_score: float = Field(default=0.0, ge=0, le=1)


# ---------------------------------------------------------------------------
# Incident Correlation (internal rule-based service, not an external team
# deliverable, but kept here for symmetry / potential future ML upgrade)
# ---------------------------------------------------------------------------
class CorrelationCandidateIncident(BaseModel):
    incident_id: uuid.UUID
    event_type: str
    latitude: float
    longitude: float
    start_time: str


class CorrelationResult(BaseModel):
    matched_incident_id: Optional[uuid.UUID] = None
    should_create_new: bool = True
    reason: str = ""

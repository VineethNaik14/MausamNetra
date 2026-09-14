import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.verification import VerificationStatus


class VerificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID
    trust_score: int
    status: VerificationStatus
    reason: Optional[str]
    verified_by: Optional[uuid.UUID]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ManualVerifyRequest(BaseModel):
    """Admin manual override of a report's verification status."""

    reason: Optional[str] = Field(default=None, max_length=1000)
    trust_score: Optional[int] = Field(default=None, ge=0, le=100)


class ManualRejectRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class EscalateRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)

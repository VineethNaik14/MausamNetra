import uuid
from datetime import datetime
from typing import Any, Optional
from app.schemas.verification import VerificationRead

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.report import ReportStatus


class ReportCreate(BaseModel):
    source_id: uuid.UUID
    text: str = Field(min_length=3, max_length=5000)
    timestamp: Optional[datetime] = None
    event_type_hint: Optional[str] = None
    
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    city: Optional[str] = Field(default=None, max_length=120)
    district: Optional[str] = Field(default=None, max_length=120)
    state: Optional[str] = Field(default=None, max_length=120)

    media_url: Optional[str] = Field(default=None, max_length=512)
    report_metadata: Optional[dict[str, Any]] = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank")
        return v.strip()


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    text: str
    event_type: Optional[str]
    event_confidence: Optional[float]
    timestamp: datetime
    latitude: float
    longitude: float
    city: Optional[str]
    district: Optional[str]
    state: Optional[str]
    media_url: Optional[str]
    report_metadata: Optional[dict[str, Any]]
    status: ReportStatus
    incident_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
        # Populated from the 1:1 Verification row once the AI pipeline has run.
    # None while status == PENDING/FAILED (pipeline hasn't produced a verdict yet).
    verification: Optional[VerificationRead] = None


class ReportFilterParams(BaseModel):
    event: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    status: Optional[ReportStatus] = None
    source_id: Optional[uuid.UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

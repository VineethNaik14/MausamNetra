import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    severity: IncidentSeverity
    latitude: float
    longitude: float
    state: Optional[str]
    district: Optional[str]
    city: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    confidence: Optional[float]
    status: IncidentStatus
    report_count: int
    verified_count: int
    suspicious_count: int
    duplicate_count: int
    created_at: datetime
    updated_at: datetime


class IncidentMapPoint(BaseModel):
    """Lightweight representation optimized for Leaflet map markers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    severity: IncidentSeverity
    status: IncidentStatus
    latitude: float
    longitude: float
    report_count: int


class IncidentFilterParams(BaseModel):
    event: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class NearbyIncidentParams(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_km: float = Field(default=10, gt=0, le=500)
    event: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None


class IncidentNearbyResult(IncidentRead):
    distance_km: float

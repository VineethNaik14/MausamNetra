from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class WeatherReport(BaseModel):
    """Canonical report shared with classification, verification and backend modules."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    source_type: str
    text: str
    event_type: Optional[str] = None
    event_confidence: Optional[float] = None
    timestamp: datetime
    latitude: float
    longitude: float
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    media_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("text")
    @classmethod
    def text_required(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("text must not be empty")
        return value

    @field_validator("latitude")
    @classmethod
    def latitude_valid(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def longitude_valid(cls, value: float) -> float:
        if not -180 <= value <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return value

    @field_validator("event_confidence")
    @classmethod
    def confidence_valid(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not 0 <= value <= 1:
            raise ValueError("event_confidence must be between 0 and 1")
        return value

"""Inbound report schema consumed by the verification engine.

This mirrors the ``Report`` object described in the backend design
document, restricted to the fields the verification engine actually
needs. The backend/database may have additional fields (e.g.
``incident relationship``, ``created_at``) that are irrelevant here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ReportSource(str, Enum):
    """Known source categories. ``UNKNOWN`` is the safe default."""

    WEATHER_API = "weather_api"
    GOVERNMENT = "government"
    VERIFIED_NEWS = "verified_news"
    CITIZEN = "citizen"
    SOCIAL_MEDIA = "social_media"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> "ReportSource":
        # Unknown/free-text source strings degrade gracefully instead of
        # raising a validation error — the source_reliability component
        # scores UNKNOWN conservatively.
        return cls.UNKNOWN


class MediaAsset(BaseModel):
    """Optional media attached to a report."""

    url: Optional[str] = Field(default=None, description="URL or storage key for the media file.")
    media_timestamp: Optional[datetime] = Field(
        default=None, description="Capture/EXIF timestamp of the media, if known."
    )
    content_type: Optional[str] = Field(
        default=None, description="MIME type, e.g. 'image/jpeg'. Required for validation if url is set."
    )
    size_bytes: Optional[int] = Field(default=None, ge=0)


class NormalizedWeatherReport(BaseModel):
    """A single normalized weather-related report/source record.

    This is the primary input contract for ``TrustEngine.verify()`` and
    the ``/api/v1/verification/verify`` endpoint.
    """

    report_id: str = Field(..., min_length=1, max_length=128)
    source: ReportSource = Field(default=ReportSource.UNKNOWN)
    text: Optional[str] = Field(default=None, max_length=5000)
    event_type: Optional[str] = Field(default=None, max_length=64)
    event_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    city: Optional[str] = Field(default=None, max_length=128)
    district: Optional[str] = Field(default=None, max_length=128)
    state: Optional[str] = Field(default=None, max_length=128)

    timestamp: datetime = Field(..., description="Time the report was submitted/observed.")
    media: Optional[MediaAsset] = Field(default=None)

    @field_validator("text")
    @classmethod
    def _strip_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None

    @field_validator("timestamp")
    @classmethod
    def _ensure_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def has_media(self) -> bool:
        return self.media is not None and bool(self.media.url)


class RelatedReport(BaseModel):
    """A minimal view of another report, used for corroboration checks.

    The verification engine never fetches these itself (see
    ``interfaces/repositories.py``) — the caller (verification service)
    supplies candidate nearby/related reports, keeping ML logic free of
    database concerns.
    """

    report_id: str
    source: ReportSource = Field(default=ReportSource.UNKNOWN)
    text: Optional[str] = None
    event_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def _ensure_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

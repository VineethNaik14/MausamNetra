import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class IncidentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Incident(Base):
    """
    An Incident represents a correlated real-world weather event, built up
    from one or more Reports by the IncidentCorrelationService.
    """

    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="longitude_range"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="confidence_range"
        ),
        Index("ix_incidents_event_type", "event_type"),
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_start_time", "start_time"),
        # NOTE: GeoAlchemy2 automatically manages a GIST spatial index on `location`
        # (idx_incidents_location) - no explicit Index() needed here.
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        String(20), nullable=False, default=IncidentSeverity.LOW, server_default=IncidentSeverity.LOW.value
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(
        String(20), nullable=False, default=IncidentStatus.ACTIVE, server_default=IncidentStatus.ACTIVE.value
    )

    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    verified_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    suspicious_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reports: Mapped[list["Report"]] = relationship("Report", back_populates="incident")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Incident id={self.id} event_type={self.event_type} severity={self.severity}>"

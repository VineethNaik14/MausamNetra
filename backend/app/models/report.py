import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReportStatus(str, enum.Enum):
    """High-level processing status of a report as it moves through the pipeline."""

    PENDING = "PENDING"          # just ingested, AI pipeline not finished
    PROCESSED = "PROCESSED"      # classification/trust/duplicate steps ran
    FAILED = "FAILED"            # AI pipeline failed at some stage; report preserved


class Report(Base):
    """
    A raw weather-related report from any source (citizen, API, news, etc).

    A Report is NOT the same as an Incident: many reports may eventually be
    correlated into a single Incident (see models/incident.py).
    """

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="longitude_range"),
        CheckConstraint(
            "event_confidence IS NULL OR (event_confidence >= 0 AND event_confidence <= 1)",
            name="event_confidence_range",
        ),
        Index("ix_reports_timestamp", "timestamp"),
        Index("ix_reports_event_type", "event_type"),
        Index("ix_reports_status", "status"),
        Index("ix_reports_state", "state"),
        Index("ix_reports_city", "city"),
        # NOTE: GeoAlchemy2 automatically manages a GIST spatial index on `location`
        # (idx_reports_location) - no explicit Index() needed here.
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Event classification (filled in by the classifier service; nullable until processed)
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    event_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Geospatial - store both raw lat/lon (for easy read/display) AND a PostGIS geography point
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)

    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    report_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[ReportStatus] = mapped_column(
        String(20), nullable=False, default=ReportStatus.PENDING, server_default=ReportStatus.PENDING.value
    )

    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped["Source"] = relationship("Source", back_populates="reports")
    incident: Mapped["Incident | None"] = relationship("Incident", back_populates="reports")
    verification: Mapped["Verification | None"] = relationship(
        "Verification", back_populates="report", uselist=False, cascade="all, delete-orphan"
    )
    duplicate_link: Mapped["Duplicate | None"] = relationship(
        "Duplicate",
        back_populates="report",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="Duplicate.report_id",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Report id={self.id} event_type={self.event_type} status={self.status}>"

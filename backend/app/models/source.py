import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SourceType(str, enum.Enum):
    CITIZEN = "citizen"
    WEATHER_API = "weather_api"
    GOVERNMENT = "government"
    NEWS = "news"
    PUBLIC_FEED = "public_feed"
    SIMULATED_SOCIAL = "simulated_social"


class Source(Base):
    """
    A data source that reports originate from.

    NOTE: reliability_score is a *prototype* heuristic value used to weight
    trust calculations in this hackathon demo. It is NOT an official IMD
    reliability rating.
    """

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0, server_default="50.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reports: Mapped[list["Report"]] = relationship("Report", back_populates="source")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Source id={self.id} name={self.name}>"

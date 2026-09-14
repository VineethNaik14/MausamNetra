import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Duplicate(Base):
    """
    Records that `report_id` is considered a duplicate of `master_report_id`.

    Duplicate reports are NEVER deleted - they are preserved for
    traceability/audit, and the relationship is simply recorded here.
    """

    __tablename__ = "duplicates"
    __table_args__ = (
        CheckConstraint("similarity_score >= 0 AND similarity_score <= 1", name="similarity_score_range"),
        CheckConstraint("report_id != master_report_id", name="duplicate_not_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    master_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report: Mapped["Report"] = relationship("Report", back_populates="duplicate_link", foreign_keys=[report_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Duplicate report_id={self.report_id} master={self.master_report_id}>"

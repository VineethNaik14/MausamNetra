import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SUSPICIOUS = "SUSPICIOUS"
    REJECTED = "REJECTED"


class Verification(Base):
    """
    Trust/verification outcome for a single Report.

    trust_score is produced by the TrustEngine abstraction (see
    services/integrations/trust_engine.py). The default score->status
    mapping used by the mock/prototype policy is:
        80-100 -> VERIFIED
        60-79  -> NEEDS_REVIEW
        0-59   -> SUSPICIOUS
    These are PROTOTYPE thresholds, not official IMD policy.
    """

    __tablename__ = "verifications"
    __table_args__ = (
        CheckConstraint("trust_score >= 0 AND trust_score <= 100", name="trust_score_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    trust_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[VerificationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=VerificationStatus.NEEDS_REVIEW,
        server_default=VerificationStatus.NEEDS_REVIEW.value,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    report: Mapped["Report"] = relationship("Report", back_populates="verification")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Verification report_id={self.report_id} status={self.status} score={self.trust_score}>"

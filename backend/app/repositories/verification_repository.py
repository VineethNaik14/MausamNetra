import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.verification import Verification, VerificationStatus


class VerificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_report_id(self, report_id: uuid.UUID) -> Optional[Verification]:
        stmt = select(Verification).where(Verification.report_id == report_id)
        return self.db.scalar(stmt)

    def upsert(self, verification: Verification) -> Verification:
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        return verification

    def count_by_status(self, status: VerificationStatus) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Verification).where(Verification.status == status)
        return self.db.scalar(stmt) or 0

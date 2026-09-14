import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source


class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, source_id: uuid.UUID) -> Optional[Source]:
        return self.db.get(Source, source_id)

    def list_active(self) -> list[Source]:
        stmt = select(Source).where(Source.is_active.is_(True))
        return list(self.db.scalars(stmt).all())

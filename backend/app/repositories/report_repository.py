import uuid
from datetime import datetime
from typing import Optional
from datetime import datetime, timedelta, timezone

from geoalchemy2 import Geography
from geoalchemy2.functions import ST_MakePoint, ST_SetSRID
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.models.report import Report, ReportStatus


def make_point(longitude: float, latitude: float):
    """Build a PostGIS geography point (SRID 4326) from lon/lat."""
    return cast(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), Geography(geometry_type="POINT", srid=4326))


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: uuid.UUID) -> Optional[Report]:
        return self.db.get(Report, report_id)

    def update(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def list_filtered(
        self,
        *,
        event: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[ReportStatus] = None,
        source_id: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Report], int]:
        stmt = select(Report)
        count_stmt = select(func.count()).select_from(Report)

        conditions = []
        if event:
            conditions.append(Report.event_type == event.upper())
        if state:
            conditions.append(func.lower(Report.state) == state.lower())
        if district:
            conditions.append(func.lower(Report.district) == district.lower())
        if city:
            conditions.append(func.lower(Report.city) == city.lower())
        if status:
            conditions.append(Report.status == status)
        if source_id:
            conditions.append(Report.source_id == source_id)
        if date_from:
            conditions.append(Report.timestamp >= date_from)
        if date_to:
            conditions.append(Report.timestamp <= date_to)

        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Report.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total

   

    def find_recent_candidates_for_duplicate_check(
        self, *, event_type: Optional[str] = None, within_hours: int = 24, limit: int = 50
    ) -> list[Report]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=within_hours)
        stmt = (
            select(Report)
            .where(Report.timestamp >= cutoff)
            .order_by(Report.timestamp.desc())
            .limit(limit)
        )
        if event_type:
            stmt = stmt.where(Report.event_type == event_type)
        return list(self.db.scalars(stmt).all())

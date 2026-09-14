import uuid
from typing import Optional

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session
from sqlalchemy.types import Float as SAFloat

from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.repositories.report_repository import make_point


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, incident: Incident) -> Incident:
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_by_id(self, incident_id: uuid.UUID) -> Optional[Incident]:
        return self.db.get(Incident, incident_id)

    def update(self, incident: Incident) -> Incident:
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def list_active_candidates(self, event_type: str) -> list[Incident]:
        """Incidents that are still ACTIVE/MONITORING, used by the correlation service."""
        stmt = select(Incident).where(
            Incident.event_type == event_type,
            Incident.status.in_([IncidentStatus.ACTIVE, IncidentStatus.MONITORING]),
        )
        return list(self.db.scalars(stmt).all())

    def list_filtered(
        self,
        *,
        event: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Incident], int]:
        stmt = select(Incident)
        count_stmt = select(func.count()).select_from(Incident)

        conditions = []
        if event:
            conditions.append(Incident.event_type == event.upper())
        if state:
            conditions.append(func.lower(Incident.state) == state.lower())
        if district:
            conditions.append(func.lower(Incident.district) == district.lower())
        if city:
            conditions.append(func.lower(Incident.city) == city.lower())
        if status:
            conditions.append(Incident.status == status)
        if severity:
            conditions.append(Incident.severity == severity)

        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = self.db.scalar(count_stmt) or 0
        stmt = stmt.order_by(Incident.start_time.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total

    def list_for_map(self, *, status: Optional[IncidentStatus] = None, limit: int = 500) -> list[Incident]:
        stmt = select(Incident).order_by(Incident.updated_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(Incident.status == status)
        else:
            stmt = stmt.where(Incident.status.in_([IncidentStatus.ACTIVE, IncidentStatus.MONITORING]))
        return list(self.db.scalars(stmt).all())

    def find_nearby(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
        event: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
    ) -> list[tuple[Incident, float]]:
        """Use PostGIS ST_DWithin (meters) + ST_Distance for nearby search."""
        origin = make_point(longitude, latitude)
        radius_m = radius_km * 1000

        distance_col = cast(ST_Distance(Incident.location, origin), SAFloat).label("distance_m")
        stmt = (
            select(Incident, distance_col)
            .where(ST_DWithin(Incident.location, origin, radius_m))
            .order_by(distance_col.asc())
        )

        if event:
            stmt = stmt.where(Incident.event_type == event.upper())
        if state:
            stmt = stmt.where(func.lower(Incident.state) == state.lower())
        if district:
            stmt = stmt.where(func.lower(Incident.district) == district.lower())
        if city:
            stmt = stmt.where(func.lower(Incident.city) == city.lower())

        rows = self.db.execute(stmt).all()
        return [(row[0], row[1] / 1000.0) for row in rows]

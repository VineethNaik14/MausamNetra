from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentStatus
from app.models.report import Report
from app.models.source import Source
from app.models.verification import Verification, VerificationStatus
from app.schemas.analytics import (
    AnalyticsResponse,
    AnalyticsSummary,
    CountByKey,
    TimeSeriesPoint,
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_analytics(self, time_series_days: int = 14) -> AnalyticsResponse:
        total_reports = self.db.scalar(select(func.count()).select_from(Report)) or 0

        verified_reports = self.db.scalar(
            select(func.count()).select_from(Verification).where(Verification.status == VerificationStatus.VERIFIED)
        ) or 0
        suspicious_reports = self.db.scalar(
            select(func.count()).select_from(Verification).where(Verification.status == VerificationStatus.SUSPICIOUS)
        ) or 0
        pending_verification = self.db.scalar(
            select(func.count())
            .select_from(Verification)
            .where(Verification.status == VerificationStatus.NEEDS_REVIEW)
        ) or 0
        rejected_reports = self.db.scalar(
            select(func.count()).select_from(Verification).where(Verification.status == VerificationStatus.REJECTED)
        ) or 0

        active_events = self.db.scalar(
            select(func.count())
            .select_from(Incident)
            .where(Incident.status.in_([IncidentStatus.ACTIVE, IncidentStatus.MONITORING]))
        ) or 0

        summary = AnalyticsSummary(
            active_events=active_events,
            total_reports=total_reports,
            verified_reports=verified_reports,
            suspicious_reports=suspicious_reports,
            pending_verification=pending_verification,
            rejected_reports=rejected_reports,
        )

        event_distribution = [
            CountByKey(key=row[0] or "UNKNOWN", count=row[1])
            for row in self.db.execute(
                select(Report.event_type, func.count()).group_by(Report.event_type)
            ).all()
        ]

        severity_distribution = [
            CountByKey(key=row[0], count=row[1])
            for row in self.db.execute(
                select(Incident.severity, func.count()).group_by(Incident.severity)
            ).all()
        ]

        source_distribution = [
            CountByKey(key=row[0], count=row[1])
            for row in self.db.execute(
                select(Source.name, func.count(Report.id))
                .join(Report, Report.source_id == Source.id)
                .group_by(Source.name)
            ).all()
        ]

        geographic_distribution = [
            CountByKey(key=row[0] or "UNKNOWN", count=row[1])
            for row in self.db.execute(
                select(Report.state, func.count()).group_by(Report.state)
            ).all()
        ]

        since = datetime.now(timezone.utc) - timedelta(days=time_series_days)
        rows = self.db.execute(
            select(func.date(Report.timestamp), func.count())
            .where(Report.timestamp >= since)
            .group_by(func.date(Report.timestamp))
            .order_by(func.date(Report.timestamp))
        ).all()
        time_series = [TimeSeriesPoint(date=str(row[0]), count=row[1]) for row in rows]

        return AnalyticsResponse(
            summary=summary,
            event_distribution=event_distribution,
            severity_distribution=severity_distribution,
            source_distribution=source_distribution,
            geographic_distribution=geographic_distribution,
            time_series=time_series,
        )

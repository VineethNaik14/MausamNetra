from typing import Optional

from pydantic import BaseModel


class CountByKey(BaseModel):
    key: str
    count: int


class TimeSeriesPoint(BaseModel):
    date: str  # ISO date (YYYY-MM-DD)
    count: int


class AnalyticsSummary(BaseModel):
    active_events: int
    total_reports: int
    verified_reports: int
    suspicious_reports: int
    pending_verification: int
    rejected_reports: int


class AnalyticsResponse(BaseModel):
    summary: AnalyticsSummary
    event_distribution: list[CountByKey]
    severity_distribution: list[CountByKey]
    source_distribution: list[CountByKey]
    geographic_distribution: list[CountByKey]  # by state
    time_series: list[TimeSeriesPoint]

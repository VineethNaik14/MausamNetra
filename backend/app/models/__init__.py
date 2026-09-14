"""
Import every model module here so that:
1. `app.db.base.Base.metadata` is fully populated for Alembic autogenerate.
2. Relationship string references (e.g. "Incident") resolve correctly.
"""
from app.models.user import User, UserRole  # noqa: F401
from app.models.source import Source, SourceType  # noqa: F401
from app.models.report import Report, ReportStatus  # noqa: F401
from app.models.incident import Incident, IncidentSeverity, IncidentStatus  # noqa: F401
from app.models.verification import Verification, VerificationStatus  # noqa: F401
from app.models.duplicate import Duplicate  # noqa: F401

__all__ = [
    "User",
    "UserRole",
    "Source",
    "SourceType",
    "Report",
    "ReportStatus",
    "Incident",
    "IncidentSeverity",
    "IncidentStatus",
    "Verification",
    "VerificationStatus",
    "Duplicate",
]

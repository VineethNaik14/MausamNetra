"""Repository abstraction for optional persistence.

The ML engine MUST be usable without a database (see tests, which run
with no repository at all). When a backend wants to persist results, it
implements this Protocol against SQLAlchemy/PostgreSQL — the ML code
never imports SQLAlchemy directly.
"""
from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from ..schemas.report import RelatedReport
from ..schemas.verification import VerificationResult


@runtime_checkable
class VerificationRepository(Protocol):
    """Persistence boundary for verification results.

    A FastAPI/SQLAlchemy-backed implementation would, for example,
    upsert into the ``Verification`` and ``Duplicate`` tables described
    in the backend design doc.
    """

    def save_result(self, result: VerificationResult) -> None:
        ...

    def get_related_reports(
        self,
        report_id: str,
        latitude: float | None,
        longitude: float | None,
        radius_km: float,
        window_hours: float,
    ) -> List[RelatedReport]:
        """Return nearby/temporally-close reports for corroboration checks.

        Geospatial filtering should use PostGIS (e.g. ``ST_DWithin``) in
        the real implementation. The verification engine only consumes
        the resulting list — it never issues SQL itself.
        """
        ...

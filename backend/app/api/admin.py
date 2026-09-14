import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db_session
from app.dependencies.services import get_report_service
from app.models.report import ReportStatus
from app.models.user import User
from app.repositories.verification_repository import VerificationRepository
from app.models.verification import VerificationStatus
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.report import ReportFilterParams, ReportRead
from app.dependencies.auth import require_admin
from app.services.report_service import ReportService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/reports",
    response_model=PaginatedResponse[ReportRead],
    summary="[ADMIN] List all reports (includes PENDING/FAILED not normally surfaced)",
)
def admin_list_reports(
    event: str | None = None,
    state: str | None = None,
    district: str | None = None,
    city: str | None = None,
    status: ReportStatus | None = None,
    page: int = 1,
    page_size: int = 20,
    admin: User = Depends(require_admin),
    report_service: ReportService = Depends(get_report_service),
):
    params = ReportFilterParams(
        event=event, state=state, district=district, city=city, status=status, page=page, page_size=page_size,
    )
    items, total = report_service.list_filtered(params)
    total_pages = (total + params.page_size - 1) // params.page_size if total else 0
    return PaginatedResponse(
        data=[ReportRead.model_validate(r) for r in items],
        pagination=PaginationMeta(page=params.page, page_size=params.page_size, total=total, total_pages=total_pages),
    )


@router.get(
    "/reports/{report_id}",
    response_model=ApiResponse[ReportRead],
    summary="[ADMIN] Get full detail of any report",
)
def admin_get_report(
    report_id: uuid.UUID,
    admin: User = Depends(require_admin),
    report_service: ReportService = Depends(get_report_service),
):
    report = report_service.get_by_id(report_id)
    return ApiResponse(data=ReportRead.model_validate(report))


@router.get("/statistics", response_model=ApiResponse[dict], summary="[ADMIN] Verification pipeline statistics")
def admin_statistics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    repo = VerificationRepository(db)
    stats = {
        "verified": repo.count_by_status(VerificationStatus.VERIFIED),
        "needs_review": repo.count_by_status(VerificationStatus.NEEDS_REVIEW),
        "suspicious": repo.count_by_status(VerificationStatus.SUSPICIOUS),
        "rejected": repo.count_by_status(VerificationStatus.REJECTED),
    }
    return ApiResponse(data=stats)

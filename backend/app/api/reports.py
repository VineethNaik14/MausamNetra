import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.dependencies.auth import require_admin
from app.dependencies.database import get_db_session
from app.dependencies.services import (
    MediaService,
    get_media_service,
    get_report_service,
    get_verification_service,
)
from app.models.report import ReportStatus
from app.models.user import User
from app.repositories.source_repository import SourceRepository
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.report import ReportCreate, ReportFilterParams, ReportRead
from app.schemas.verification import (
    EscalateRequest,
    ManualRejectRequest,
    ManualVerifyRequest,
    VerificationRead,
)
from app.services.report_service import ReportService
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/upload-media",
    response_model=ApiResponse[dict],
    summary="Upload a photo/video to attach to a report",
)
async def upload_media(
    file: UploadFile = File(...),
    media_service: MediaService = Depends(get_media_service),
):
    path = await media_service.save_upload(file)
    return ApiResponse(data={"media_url": path}, message="File uploaded successfully")


@router.post("", response_model=ApiResponse[ReportRead], summary="Submit a new weather report")
async def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db_session),
    report_service: ReportService = Depends(get_report_service),
):
    source = SourceRepository(db).get_by_id(payload.source_id)
    if source is None or not source.is_active:
        raise ValidationError("Invalid or inactive source_id")

    report = await report_service.create_report(
        payload,
        source_reliability=source.reliability_score,
        source_type=source.type.value if hasattr(source.type, "value") else source.type,
    )
    return ApiResponse(data=ReportRead.model_validate(report), message="Report created successfully")


@router.get("", response_model=PaginatedResponse[ReportRead], summary="List reports with filters and pagination")
def list_reports(
    event: str | None = None,
    state: str | None = None,
    district: str | None = None,
    city: str | None = None,
    status: ReportStatus | None = None,
    source_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    report_service: ReportService = Depends(get_report_service),
):
    params = ReportFilterParams(
        event=event,
        state=state,
        district=district,
        city=city,
        status=status,
        source_id=source_id,
        page=page,
        page_size=page_size,
    )
    items, total = report_service.list_filtered(params)
    total_pages = (total + params.page_size - 1) // params.page_size if total else 0
    return PaginatedResponse(
        data=[ReportRead.model_validate(r) for r in items],
        pagination=PaginationMeta(page=params.page, page_size=params.page_size, total=total, total_pages=total_pages),
    )


@router.get("/{report_id}", response_model=ApiResponse[ReportRead], summary="Get a single report by id")
def get_report(
    report_id: uuid.UUID,
    report_service: ReportService = Depends(get_report_service),
):
    report = report_service.get_by_id(report_id)
    return ApiResponse(data=ReportRead.model_validate(report))


@router.post(
    "/{report_id}/verify",
    response_model=ApiResponse[VerificationRead],
    summary="[ADMIN] Manually verify a report",
)
async def verify_report(
    report_id: uuid.UUID,
    payload: ManualVerifyRequest,
    admin: User = Depends(require_admin),
    verification_service: VerificationService = Depends(get_verification_service),
):
    verification = await verification_service.verify(report_id, admin.id, payload)
    return ApiResponse(data=VerificationRead.model_validate(verification), message="Report verified")


@router.post(
    "/{report_id}/reject",
    response_model=ApiResponse[VerificationRead],
    summary="[ADMIN] Reject a report",
)
async def reject_report(
    report_id: uuid.UUID,
    payload: ManualRejectRequest,
    admin: User = Depends(require_admin),
    verification_service: VerificationService = Depends(get_verification_service),
):
    verification = await verification_service.reject(report_id, admin.id, payload)
    return ApiResponse(data=VerificationRead.model_validate(verification), message="Report rejected")


@router.post(
    "/{report_id}/escalate",
    response_model=ApiResponse[VerificationRead],
    summary="[ADMIN] Escalate a report for further review",
)
def escalate_report(
    report_id: uuid.UUID,
    payload: EscalateRequest,
    admin: User = Depends(require_admin),
    verification_service: VerificationService = Depends(get_verification_service),
):
    verification = verification_service.escalate(report_id, admin.id, payload.reason)
    return ApiResponse(data=VerificationRead.model_validate(verification), message="Report escalated for review")

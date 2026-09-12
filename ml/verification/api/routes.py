"""FastAPI routes: /api/v1/verification/*

Kept thin — all real logic lives in ``services/verification_service.py``
and the ``TrustEngine``. Routes only: validate input, call the service,
translate domain exceptions into safe HTTP responses (no stack traces).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from ..config import get_settings
from ..exceptions import InvalidReportError, UnsupportedMediaError, VerificationError
from ..logging_config import get_logger
from ..schemas.report import NormalizedWeatherReport, RelatedReport
from ..schemas.verification import BatchVerificationResult, VerificationResult
from .dependencies import get_verification_service
from ..services.verification_service import VerificationService

logger = get_logger("api.routes")

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])


class VerifyRequest(BaseModel):
    report: NormalizedWeatherReport
    related_reports: list[RelatedReport] = Field(default_factory=list)


class BatchVerifyRequest(BaseModel):
    reports: list[NormalizedWeatherReport]


class SimilarityRequest(BaseModel):
    text_a: str = Field(..., min_length=1, max_length=5000)
    text_b: str = Field(..., min_length=1, max_length=5000)


class SimilarityResponse(BaseModel):
    similarity: float


class HealthResponse(BaseModel):
    status: str
    classifier_configured: bool
    similarity_backend: str


@router.post("/verify", response_model=VerificationResult)
def verify_report(
    payload: VerifyRequest,
    service: VerificationService = Depends(get_verification_service),
) -> VerificationResult:
    try:
        return service.verify_report(payload.report, related_reports=payload.related_reports)
    except InvalidReportError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except VerificationError as exc:
        logger.error("verify_failed report_id=%s error=%s", payload.report.report_id, exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed") from exc
    except Exception as exc:  # noqa: BLE001 - never leak internals to the client
        logger.exception("unexpected_verify_error report_id=%s", payload.report.report_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal verification error"
        ) from exc


@router.post("/verify/with-image", response_model=VerificationResult)
async def verify_report_with_image(
    report_json: str = Form(..., description="JSON-encoded NormalizedWeatherReport"),
    related_reports_json: str = Form(default="[]", description="JSON-encoded list of RelatedReport"),
    image: UploadFile = File(...),
    service: VerificationService = Depends(get_verification_service),
) -> VerificationResult:
    settings = get_settings()

    try:
        report = NormalizedWeatherReport.model_validate(json.loads(report_json))
        related_reports = [RelatedReport.model_validate(r) for r in json.loads(related_reports_json)]
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON payload") from exc

    max_bytes = int(settings.max_image_size_mb * 1024 * 1024)
    image_bytes = await image.read(max_bytes + 1)
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {settings.max_image_size_mb} MB limit",
        )

    try:
        return service.verify_report(report, related_reports=related_reports, image_bytes=image_bytes)
    except UnsupportedMediaError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc
    except VerificationError as exc:
        logger.error("verify_with_image_failed report_id=%s error=%s", report.report_id, exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("unexpected_verify_with_image_error report_id=%s", report.report_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal verification error"
        ) from exc


@router.post("/batch", response_model=BatchVerificationResult)
def verify_batch(
    payload: BatchVerifyRequest,
    service: VerificationService = Depends(get_verification_service),
) -> BatchVerificationResult:
    if len(payload.reports) > 200:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Batch size exceeds the maximum of 200 reports per request",
        )
    return service.verify_batch(payload.reports)


@router.post("/similarity", response_model=SimilarityResponse)
def compute_similarity(
    payload: SimilarityRequest,
    service: VerificationService = Depends(get_verification_service),
) -> SimilarityResponse:
    similarity = service.engine.similarity_engine.compare_reports(payload.text_a, payload.text_b)
    return SimilarityResponse(similarity=round(similarity, 4))


@router.get("/health", response_model=HealthResponse)
def health(service: VerificationService = Depends(get_verification_service)) -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        classifier_configured=service.engine.classifier is not None,
        similarity_backend=settings.similarity_backend,
    )

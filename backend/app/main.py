import os
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.api.websocket import router as websocket_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach a request id for tracing and log basic request timing."""
    request_id = str(uuid.uuid4())
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s (%.1fms) [request_id=%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


# --- Centralized exception handling -----------------------------------------

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                # jsonable_encoder is required here: pydantic v2 error dicts
                # can include a raw exception instance under ctx.error (for
                # validators that raise ValueError), which json.dumps cannot
                # serialize on its own.
                "details": jsonable_encoder(exc.errors()),
            },
        },
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    # Raised when a route builds a Pydantic model (e.g. a *FilterParams
    # schema) from query params inside the function body rather than via
    # FastAPI's own request parsing. Treated the same as any other
    # validation failure - 422, no internal details beyond field errors.
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": jsonable_encoder(exc.errors()),
            },
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces / internal details to the client.
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"},
        },
    )


# --- Routes -------------------------------------------------------------------

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket_router)

# Serve uploaded media as static files (prototype only - swap for S3/MinIO + CDN in production).
# StaticFiles raises at import time if the directory doesn't exist yet (e.g. a
# fresh checkout, since git doesn't track empty folders) - create it first so
# the app (and test collection) doesn't crash before startup even runs.
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Health"], summary="Basic liveness check")
def root():
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"], summary="Health check")
def health():
    return {"status": "healthy"}


@app.on_event("startup")
async def on_startup():
    logger.info("%s v%s starting up (environment=%s)", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("%s shutting down", settings.PROJECT_NAME)

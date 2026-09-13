"""Standalone ASGI app for running/demoing the verification service on its own.

In the real MausamNetra backend, you'd instead do:

    from ml.verification.api.routes import router as verification_router
    app.include_router(verification_router)

inside the team's main FastAPI app. This file exists so the module can
also be run and tested independently (``uvicorn main:app``).
"""
from fastapi import FastAPI

from ml.verification.api.routes import router as verification_router
from ml.verification.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title="MausamNetra Verification & Trust Engine",
    version="0.1.0",
    description="AI/ML verification microservice — trust scoring, duplicate and suspicious-report detection.",
)
app.include_router(verification_router)


@app.get("/")
def root() -> dict:
    return {"service": "mausamnetra-verification", "docs": "/docs"}

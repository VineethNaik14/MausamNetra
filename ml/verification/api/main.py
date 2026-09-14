"""Runnable entrypoint for the Verification / Trust Engine microservice.

The backend's RealTrustEngine (mausamnetra_backend/app/services/integrations/
real_trust_engine.py) expects this service to be reachable at
VERIFICATION_SERVICE_URL (default http://localhost:8001) and to expose
POST /api/v1/verification/verify.

Run with (from the repo root, verification service's own dependencies
installed - see requirements.txt at repo root):

    uvicorn ml.verification.api.main:app --port 8001 --reload

Only this file's job is to build the FastAPI() app and mount the router -
all real logic lives in routes.py / services/verification_service.py /
engine/trust_engine.py, unchanged.
"""

from fastapi import FastAPI

from . import routes

app = FastAPI(
    title="MausamNetra Verification / Trust Engine",
    description=(
        "AI-assisted evidence-based reliability scoring for weather reports. "
        "Prototype decision-support only - not an official IMD certification."
    ),
)
app.include_router(routes.router)


@app.get("/health")
def root_health() -> dict:
    """Plain top-level health check (separate from /api/v1/verification/health,
    which also reports classifier wiring) - useful for simple liveness probes."""
    return {"status": "ok"}

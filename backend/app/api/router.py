from fastapi import APIRouter

from app.api import admin, analytics, auth, events, reports, sources

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(reports.router)
api_router.include_router(events.router)
api_router.include_router(analytics.router)
api_router.include_router(admin.router)
api_router.include_router(sources.router)
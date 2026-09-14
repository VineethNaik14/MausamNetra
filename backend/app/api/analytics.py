from fastapi import APIRouter, Depends


from app.dependencies.services import get_analytics_service

from app.schemas.analytics import AnalyticsResponse
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=ApiResponse[AnalyticsResponse], summary="Dashboard analytics/metrics")
def get_analytics(
    time_series_days: int = 14,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    data = analytics_service.get_analytics(time_series_days=time_series_days)
    return ApiResponse(data=data)

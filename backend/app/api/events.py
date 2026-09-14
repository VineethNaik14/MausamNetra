import uuid

from fastapi import APIRouter, Depends, Query


from app.dependencies.services import get_incident_service
from app.models.incident import IncidentSeverity, IncidentStatus

from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.incident import (
    IncidentFilterParams,
    IncidentMapPoint,
    IncidentNearbyResult,
    IncidentRead,
    NearbyIncidentParams,
)
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/events", tags=["Events / Incidents"])


@router.get("", response_model=PaginatedResponse[IncidentRead], summary="List incidents with filters and pagination")
def list_events(
    event: str | None = None,
    state: str | None = None,
    district: str | None = None,
    city: str | None = None,
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    page: int = 1,
    page_size: int = 20,
    incident_service: IncidentService = Depends(get_incident_service),
):
    params = IncidentFilterParams(
        event=event, state=state, district=district, city=city, status=status, severity=severity,
        page=page, page_size=page_size,
    )
    items, total = incident_service.list_filtered(params)
    total_pages = (total + params.page_size - 1) // params.page_size if total else 0
    return PaginatedResponse(
        data=[IncidentRead.model_validate(i) for i in items],
        pagination=PaginationMeta(page=params.page, page_size=params.page_size, total=total, total_pages=total_pages),
    )


@router.get("/map", response_model=ApiResponse[list[IncidentMapPoint]], summary="Optimized incident data for map display")
def get_map_data(
    incident_service: IncidentService = Depends(get_incident_service),
):
    incidents = incident_service.list_for_map()
    return ApiResponse(data=[IncidentMapPoint.model_validate(i) for i in incidents])


@router.get("/nearby", response_model=ApiResponse[list[IncidentNearbyResult]], summary="Find incidents within a radius (PostGIS ST_DWithin)")
def get_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=500),
    event: str | None = None,
    state: str | None = None,
    district: str | None = None,
    city: str | None = None,
    incident_service: IncidentService = Depends(get_incident_service),
):
    params = NearbyIncidentParams(
        latitude=latitude, longitude=longitude, radius_km=radius_km,
        event=event, state=state, district=district, city=city,
    )
    results = incident_service.find_nearby(params)
    data = [
        IncidentNearbyResult(**IncidentRead.model_validate(incident).model_dump(), distance_km=round(distance, 3))
        for incident, distance in results
    ]
    return ApiResponse(data=data)


@router.get("/{event_id}", response_model=ApiResponse[IncidentRead], summary="Get a single incident by id")
def get_event(
    event_id: uuid.UUID,
    incident_service: IncidentService = Depends(get_incident_service),
):
    incident = incident_service.get_by_id(event_id)
    return ApiResponse(data=IncidentRead.model_validate(incident))

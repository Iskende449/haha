from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.models.models import User
from app.schemas.explorer_schemas import (
    ExplorerLocationDetail,
    ExplorerLocationsResponse,
    ExplorerRouteRequest,
    ExplorerRouteResponse,
)
from app.services.heritage_catalog_service import heritage_catalog_service
from app.services.routing_service import build_navigation_meta, build_route_briefing, get_route_data, get_traffic_insight

router = APIRouter(prefix='/explorer', tags=['explorer'])


@router.get('/locations', response_model=ExplorerLocationsResponse)
async def list_locations(current_user: User = Depends(get_current_user)) -> ExplorerLocationsResponse:  # noqa: ARG001
    items, source_provider = await heritage_catalog_service.list_locations()
    mapped_count = sum(1 for item in items if item.route_available)
    return ExplorerLocationsResponse(
        items=items,
        count=len(items),
        mapped_count=mapped_count,
        source_provider=source_provider,
    )


@router.get('/locations/{source_id}', response_model=ExplorerLocationDetail)
async def get_location(
    source_id: int,
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> ExplorerLocationDetail:
    detail = await heritage_catalog_service.get_location_detail(source_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Location not found')
    return detail


@router.post('/route', response_model=ExplorerRouteResponse)
async def build_explorer_route(
    body: ExplorerRouteRequest,
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> ExplorerRouteResponse:
    location = await heritage_catalog_service.get_location_detail(body.source_id)
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Location not found')
    if location.latitude is None or location.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='This place is in the catalog, but its route point is not available yet.',
        )

    route = await get_route_data(
        start_lat=body.user_lat,
        start_lon=body.user_lon,
        end_lat=location.latitude,
        end_lon=location.longitude,
        transport_type=body.transport_mode,
        locale=body.locale,
        route_style=body.route_style,
    )
    traffic = await get_traffic_insight(
        transport_type=body.transport_mode,
        route=route,
        start_lat=body.user_lat,
        start_lon=body.user_lon,
        end_lat=location.latitude,
        end_lon=location.longitude,
        locale=body.locale,
    )
    effective_duration_s = (
        route['duration_s']
        if traffic.get('applied_to_eta', False)
        else route['duration_s'] + traffic.get('delay_minutes', 0) * 60
    )
    navigation = build_navigation_meta(
        duration_s=effective_duration_s,
        typical_duration_s=route.get('typical_duration_s'),
        distance_m=route['distance_m'],
        traffic=traffic,
        transport_type=body.transport_mode,
        route_style=body.route_style,
        alternatives_count=route.get('alternatives_count', 0),
        steps=route.get('steps', []),
    )
    analysis, voice_script = build_route_briefing(
        location_name=location.name,
        transport_type=body.transport_mode,
        route_style=body.route_style,
        locale=body.locale,
        distance_m=route['distance_m'],
        duration_s=effective_duration_s,
        traffic=traffic,
        steps=route.get('steps', []),
        provider=route['provider'],
        connector_summary=route.get('connector_summary'),
    )

    return ExplorerRouteResponse(
        location=location,
        route_geometry=route['geometry'],
        distance_m=round(route['distance_m'], 1),
        duration_s=round(effective_duration_s, 1),
        typical_duration_s=round(route.get('typical_duration_s', effective_duration_s), 1),
        traffic_delay_minutes=traffic.get('delay_minutes', 0),
        transport_mode=body.transport_mode,
        route_style=body.route_style,
        provider=route['provider'],
        traffic=traffic,
        navigation=navigation,
        analysis=analysis,
        voice_script=voice_script,
        steps=route.get('steps', []),
    )

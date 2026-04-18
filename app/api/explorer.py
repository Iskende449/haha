from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.models.models import User
from app.schemas.explorer_schemas import (
    ExplorerBootstrapResponse,
    ExplorerCatalogAppliedFilters,
    ExplorerLocationDetail,
    ExplorerLocationsResponse,
    ExplorerRouteRequest,
    ExplorerRouteResponse,
    LocationSortMode,
)
from app.services.explorer_experience_service import (
    build_bootstrap_response,
    build_render_segments,
    build_route_legend,
    build_viewport,
    build_voice_guidance,
)
from app.services.heritage_catalog_service import heritage_catalog_service
from app.services.routing_service import build_navigation_meta, build_route_briefing, get_route_data, get_traffic_insight

router = APIRouter(prefix='/explorer', tags=['explorer'])


@router.get('/bootstrap', response_model=ExplorerBootstrapResponse)
async def explorer_bootstrap() -> ExplorerBootstrapResponse:
    return build_bootstrap_response()


@router.get('/locations', response_model=ExplorerLocationsResponse)
async def list_locations(
    query: str | None = Query(None, max_length=120),
    kind: str = Query('all', pattern='^(all|petroglyph|sacred_site|calendar_event)$'),
    terrain: str = Query('all', pattern='^(all|mountain|lake|valley|steppe|city)$'),
    verified_only: bool = False,
    route_ready_only: bool = False,
    sort: LocationSortMode = 'smart',
    limit: int = Query(100, ge=1, le=250),
    offset: int = Query(0, ge=0),
    user_lat: float | None = Query(None, ge=-90, le=90),
    user_lon: float | None = Query(None, ge=-180, le=180),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> ExplorerLocationsResponse:
    items, source_provider, total_count = await heritage_catalog_service.query_locations(
        query=query,
        kind=kind,
        terrain=terrain,
        verified_only=verified_only,
        route_ready_only=route_ready_only,
        sort=sort,
        limit=limit,
        offset=offset,
        user_lat=user_lat,
        user_lon=user_lon,
    )
    mapped_count = sum(1 for item in items if item.route_available)
    featured_count = sum(1 for item in items if item.featured)
    recommended_source_id = next((item.source_id for item in items if item.route_available), None)
    if recommended_source_id is None and items:
        recommended_source_id = items[0].source_id

    return ExplorerLocationsResponse(
        items=items,
        count=len(items),
        total_count=total_count,
        mapped_count=mapped_count,
        featured_count=featured_count,
        source_provider=source_provider,
        recommended_source_id=recommended_source_id,
        applied_filters=ExplorerCatalogAppliedFilters(
            query=query,
            kind=kind,
            terrain=terrain,
            verified_only=verified_only,
            route_ready_only=route_ready_only,
            sort=sort,
            limit=limit,
            offset=offset,
            user_lat=user_lat,
            user_lon=user_lon,
        ),
    )


@router.get('/locations/{source_id}', response_model=ExplorerLocationDetail)
async def get_location(
    source_id: int,
    user_lat: float | None = Query(None, ge=-90, le=90),
    user_lon: float | None = Query(None, ge=-180, le=180),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> ExplorerLocationDetail:
    detail = await heritage_catalog_service.get_location_detail(
        source_id,
        user_lat=user_lat,
        user_lon=user_lon,
    )
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Location not found')
    return detail


@router.post('/route', response_model=ExplorerRouteResponse)
async def build_explorer_route(
    body: ExplorerRouteRequest,
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> ExplorerRouteResponse:
    location = await heritage_catalog_service.get_location_detail(
        body.source_id,
        user_lat=body.user_lat,
        user_lon=body.user_lon,
    )
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
    render_segments = build_render_segments(route_geometry=route['geometry'], transport_mode=body.transport_mode)
    viewport = build_viewport(
        route_geometry=route['geometry'],
        render_segments=render_segments,
        selected_lat=location.latitude,
        selected_lon=location.longitude,
        user_lat=body.user_lat,
        user_lon=body.user_lon,
    )
    legend = build_route_legend(
        transport_mode=body.transport_mode,
        locale=body.locale,
        render_segments=render_segments,
    )
    voice_guidance = build_voice_guidance(text=voice_script, locale=body.locale)

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
        render_segments=render_segments,
        viewport=viewport,
        legend=legend,
        voice_guidance=voice_guidance,
    )

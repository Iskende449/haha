from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.functions import ST_DistanceSphere, ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.nomadic_calendar import get_kyrgyz_month_name
from app.models.models import Location, User
from app.schemas.route_schemas import RouteRequest, RouteResponse
from app.services.ai_service import ai_service
from app.services.routing_service import get_route_polyline

router = APIRouter(prefix='/route', tags=['routing'])


@router.post('', response_model=RouteResponse)
async def build_route(
    body: RouteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteResponse:
    user_point = ST_SetSRID(ST_MakePoint(body.user_lon, body.user_lat), 4326)

    # Base query for locations
    stmt = (
        select(
            Location,
            ST_DistanceSphere(Location.geom, user_point).label('distance_m'),
            func.ST_Y(Location.geom).label('lat'),
            func.ST_X(Location.geom).label('lon'),
        )
    )

    # Filter by interests if specified (e.g., ['petroglyph'])
    if body.interests:
        stmt = stmt.where(Location.category.in_(body.interests))

    # Search by name hint if provided
    if body.destination_name:
        stmt = stmt.where(Location.name.ilike(f'%{body.destination_name}%'))

    # Sort by proximity
    stmt = stmt.order_by('distance_m').limit(1)

    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No location matching your interests found nearby.')

    location = row.Location
    distance_m = float(row.distance_m)
    dest_lat = float(row.lat)
    dest_lon = float(row.lon)

    # Nomadic Calendar & AI Logic
    kyrgyz_month = get_kyrgyz_month_name(date.today())
    
    # Seasonal recommendation logic
    seasonal_rec = ""
    if kyrgyz_month in ['Жетинин айы', 'Бештин айы', 'Үркер']:  # Late autumn/Winter/Early spring
        seasonal_rec = (
            f"It is the season of {kyrgyz_month}. High mountain passes like Saimaluu-Tash might be blocked by snow, "
            "but the lower valley petroglyphs and sacred mazars are waiting for your prayer."
        )
    else:
        seasonal_rec = (
            f"Nature is in full bloom during {kyrgyz_month}. The high spirits of the mountains are open "
            "for those who seek wisdom in the ancient carvings."
        )

    ai_blessing = await ai_service.generate_nomadic_blessing(kyrgyz_month, location.name)

    route_geometry = await get_route_polyline(
        start_lat=body.user_lat,
        start_lon=body.user_lon,
        end_lat=dest_lat,
        end_lon=dest_lon,
        transport_type=body.transport_type,
    )

    return RouteResponse(
        destination={
            'id': location.id,
            'name': location.name,
            'description': location.description,
            'category': location.category.value,
            'latitude': dest_lat,
            'longitude': dest_lon,
            'distance_m': round(distance_m, 1),
            'image_url': location.image_url,
        },
        route_geometry=route_geometry,
        nomadic_context={
            'kyrgyz_month': kyrgyz_month,
            'traveler': current_user.full_name,
        },
        ai_blessing=ai_blessing,
        seasonal_recommendation=seasonal_rec
    )

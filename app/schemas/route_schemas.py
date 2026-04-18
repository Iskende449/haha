from typing import Any

from pydantic import BaseModel, Field

from app.models.models import LocationCategory


class RouteRequest(BaseModel):
    user_lon: float = Field(..., ge=-180, le=180)
    user_lat: float = Field(..., ge=-90, le=90)
    transport_type: str = Field('car', pattern='^(car|bike|foot)$')
    duration_hours: int = Field(3, ge=1, le=24)
    interests: list[str] = Field(default=['petroglyph', 'mazar'])
    destination_name: str | None = Field(None, description='Optional destination name hint')


class RouteResponse(BaseModel):
    destination: dict[str, Any]
    route_geometry: dict[str, Any]
    nomadic_context: dict[str, str]
    ai_blessing: str
    seasonal_recommendation: str | None = None


class CheckinRequest(BaseModel):
    location_id: int = Field(..., gt=0)
    user_lon: float = Field(..., ge=-180, le=180)
    user_lat: float = Field(..., ge=-90, le=90)
    legend_answer: str | None = Field(
        None,
        description="Answer for the Legend Quest riddle required to complete check-in",
    )


class CheckinResponse(BaseModel):
    status: str
    message: str
    experience_points: int
    legend_quest: str | None = None


class DestinationSummary(BaseModel):
    id: int
    name: str
    description: str | None
    category: LocationCategory
    latitude: float
    longitude: float
    distance_m: float

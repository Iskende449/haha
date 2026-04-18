from typing import Any, Literal

from pydantic import BaseModel, Field


LocaleCode = Literal['ru', 'en', 'ky']
TransportMode = Literal['car', 'bike', 'foot']
LocationKind = Literal['petroglyph', 'sacred_site', 'calendar_event']
RouteStyle = Literal['smart']


class ExplorerLocationSummary(BaseModel):
    source_id: int
    name: str
    region: str
    summary: str
    image_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    coordinate_quality: Literal['verified', 'approximate', 'missing']
    kind: LocationKind = 'petroglyph'
    terrain: str = 'mountain'
    seasonality: str = 'all_season'
    travel_tags: list[str] = Field(default_factory=list)
    featured: bool = False
    route_available: bool = False
    source_url: str


class ExplorerLocationDetail(ExplorerLocationSummary):
    gallery: list[str] = Field(default_factory=list)
    archaeological_description: str | None = None
    ethnographic_description: str | None = None
    source_provider: str = 'fallback'


class ExplorerLocationsResponse(BaseModel):
    items: list[ExplorerLocationSummary]
    count: int
    mapped_count: int
    source_provider: str


class ExplorerRouteRequest(BaseModel):
    source_id: int = Field(..., gt=0)
    user_lat: float = Field(..., ge=-90, le=90)
    user_lon: float = Field(..., ge=-180, le=180)
    transport_mode: TransportMode = 'car'
    locale: LocaleCode = 'ru'
    route_style: RouteStyle = 'smart'


class ExplorerRouteStep(BaseModel):
    instruction: str
    distance_m: float
    duration_s: float
    maneuver_type: str
    modifier: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    voice_announcement: str | None = None


class ExplorerRouteResponse(BaseModel):
    location: ExplorerLocationDetail
    route_geometry: dict[str, Any]
    distance_m: float
    duration_s: float
    typical_duration_s: float | None = None
    traffic_delay_minutes: int = 0
    transport_mode: TransportMode
    route_style: RouteStyle
    provider: str
    traffic: dict[str, Any]
    navigation: dict[str, Any]
    analysis: str
    voice_script: str
    steps: list[ExplorerRouteStep] = Field(default_factory=list)

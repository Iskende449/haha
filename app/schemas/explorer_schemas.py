from typing import Any, Literal

from pydantic import BaseModel, Field


LocaleCode = Literal['ru', 'en', 'ky']
TransportMode = Literal['car', 'bike', 'foot']
LocationKind = Literal['petroglyph', 'sacred_site', 'calendar_event']
RouteStyle = Literal['smart']
LocationSortMode = Literal['smart', 'distance', 'name']
MapTheme = Literal['night', 'dawn']


class ExplorerMediaAsset(BaseModel):
    hero_image_url: str | None = None
    thumbnail_url: str | None = None
    gallery: list[str] = Field(default_factory=list)
    gallery_count: int = 0
    has_gallery: bool = False
    placeholder_tone: Literal['stone', 'ember', 'sun'] = 'stone'


class ExplorerMarkerPresentation(BaseModel):
    kind: LocationKind
    accent: str
    icon_key: str
    default_size: int = 34
    active_size: int = 42


class ExplorerChoiceOption(BaseModel):
    id: str
    label: str
    description: str | None = None
    accent: str | None = None
    icon_key: str | None = None


class ExplorerTransportOption(BaseModel):
    id: TransportMode
    label: str
    accent: str
    description: str


class ExplorerVoiceConfig(BaseModel):
    enabled_by_default: bool = True
    preferred_voice_gender: Literal['male'] = 'male'
    rate: float = 0.94
    pitch: float = 0.82
    volume: float = 1.0


class ExplorerMapThemeDefinition(BaseModel):
    id: MapTheme
    label: str
    description: str
    tile_url: str
    attribution: str
    tile_size: int | None = None
    zoom_offset: int | None = None
    max_zoom: int = 19
    requires_token: bool = False


class ExplorerMapConfig(BaseModel):
    default_center: list[float] = Field(default_factory=lambda: [42.8746, 74.6122])
    default_zoom: int = 8
    themes: list[ExplorerMapThemeDefinition] = Field(default_factory=list)


class ExplorerClientDefaults(BaseModel):
    locale: LocaleCode = 'ru'
    map_theme: MapTheme = 'night'
    voice_enabled: bool = True
    location_sort: LocationSortMode = 'smart'
    user_position: list[float] = Field(default_factory=lambda: [42.8746, 74.6122])


class ExplorerRouteLegendItem(BaseModel):
    id: str
    title: str
    description: str
    stroke_color: str
    outline_color: str
    dash_pattern: str | None = None
    weight: int = 6


class ExplorerRouteRenderingConfig(BaseModel):
    recommended_route_style: RouteStyle = 'smart'
    segment_presets: list[ExplorerRouteLegendItem] = Field(default_factory=list)


class ExplorerBootstrapResponse(BaseModel):
    app_name: str
    defaults: ExplorerClientDefaults
    voice: ExplorerVoiceConfig
    map: ExplorerMapConfig
    kinds: list[ExplorerChoiceOption] = Field(default_factory=list)
    terrains: list[ExplorerChoiceOption] = Field(default_factory=list)
    sort_modes: list[ExplorerChoiceOption] = Field(default_factory=list)
    transports: list[ExplorerTransportOption] = Field(default_factory=list)
    markers: list[ExplorerMarkerPresentation] = Field(default_factory=list)
    route_rendering: ExplorerRouteRenderingConfig


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
    distance_from_user_m: float | None = None
    media: ExplorerMediaAsset = Field(default_factory=ExplorerMediaAsset)
    map_marker: ExplorerMarkerPresentation | None = None
    badges: list[str] = Field(default_factory=list)


class ExplorerLocationDetail(ExplorerLocationSummary):
    gallery: list[str] = Field(default_factory=list)
    archaeological_description: str | None = None
    ethnographic_description: str | None = None
    source_provider: str = 'fallback'


class ExplorerCatalogAppliedFilters(BaseModel):
    query: str | None = None
    kind: str = 'all'
    terrain: str = 'all'
    verified_only: bool = False
    route_ready_only: bool = False
    sort: LocationSortMode = 'smart'
    limit: int = 100
    offset: int = 0
    user_lat: float | None = None
    user_lon: float | None = None


class ExplorerLocationsResponse(BaseModel):
    items: list[ExplorerLocationSummary]
    count: int
    total_count: int
    mapped_count: int
    featured_count: int
    source_provider: str
    recommended_source_id: int | None = None
    applied_filters: ExplorerCatalogAppliedFilters


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


class ExplorerRenderSegment(BaseModel):
    id: str
    kind: str
    mode: TransportMode
    transport_context: TransportMode
    label: str | None = None
    source: str | None = None
    dashed: bool = False
    distance_m: float
    duration_s: float
    coordinates: list[list[float]] = Field(default_factory=list)
    stroke_color: str
    outline_color: str
    dash_pattern: str | None = None
    weight: int = 6
    opacity: float = 1.0


class ExplorerMapViewport(BaseModel):
    mode: Literal['fit_route', 'focus_destination', 'focus_user']
    center: list[float]
    bounds: list[list[float]] | None = None
    zoom: int = 8
    mobile_zoom: int | None = None
    desktop_zoom: int | None = None
    max_zoom: int | None = None
    mobile_padding_top_left: list[int] = Field(default_factory=lambda: [24, 132])
    mobile_padding_bottom_right: list[int] = Field(default_factory=lambda: [24, 220])
    desktop_padding_top_left: list[int] = Field(default_factory=lambda: [380, 40])
    desktop_padding_bottom_right: list[int] = Field(default_factory=lambda: [40, 40])


class ExplorerVoiceGuidance(BaseModel):
    text: str
    locale: LocaleCode
    preferred_voice_gender: Literal['male'] = 'male'
    rate: float = 0.94
    pitch: float = 0.82
    volume: float = 1.0
    auto_play: bool = True


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
    render_segments: list[ExplorerRenderSegment] = Field(default_factory=list)
    viewport: ExplorerMapViewport
    legend: list[ExplorerRouteLegendItem] = Field(default_factory=list)
    voice_guidance: ExplorerVoiceGuidance

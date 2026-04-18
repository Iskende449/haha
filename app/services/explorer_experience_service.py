import math
from typing import Any

from app.core.config import settings
from app.schemas.explorer_schemas import (
    ExplorerBootstrapResponse,
    ExplorerChoiceOption,
    ExplorerClientDefaults,
    ExplorerMapConfig,
    ExplorerMapThemeDefinition,
    ExplorerMapViewport,
    ExplorerMarkerPresentation,
    ExplorerMediaAsset,
    ExplorerRenderSegment,
    ExplorerRouteLegendItem,
    ExplorerRouteRenderingConfig,
    ExplorerTransportOption,
    ExplorerVoiceConfig,
    ExplorerVoiceGuidance,
    LocationKind,
    LocaleCode,
    MapTheme,
    TransportMode,
)

DEFAULT_CENTER = [42.8746, 74.6122]

KIND_OPTIONS = {
    'all': ExplorerChoiceOption(id='all', label='Все точки', accent='#f7efe3', icon_key='sparkles'),
    'petroglyph': ExplorerChoiceOption(id='petroglyph', label='Петроглифы', accent='#f4c95d', icon_key='sun'),
    'sacred_site': ExplorerChoiceOption(id='sacred_site', label='Сакральные места', accent='#ff7b37', icon_key='flame'),
    'calendar_event': ExplorerChoiceOption(id='calendar_event', label='Традиционный календарь', accent='#ffe36c', icon_key='moon'),
}

TERRAIN_OPTIONS = {
    'all': ExplorerChoiceOption(id='all', label='Любой рельеф'),
    'mountain': ExplorerChoiceOption(id='mountain', label='Горы'),
    'lake': ExplorerChoiceOption(id='lake', label='Озеро'),
    'valley': ExplorerChoiceOption(id='valley', label='Долина'),
    'steppe': ExplorerChoiceOption(id='steppe', label='Степь'),
    'city': ExplorerChoiceOption(id='city', label='Город'),
}

SORT_OPTIONS = {
    'smart': ExplorerChoiceOption(
        id='smart',
        label='Умная выдача',
        description='Сначала featured и точки с доступным маршрутом, затем ближайшие.',
    ),
    'distance': ExplorerChoiceOption(
        id='distance',
        label='По расстоянию',
        description='Сортировка по прямой дистанции от пользователя.',
    ),
    'name': ExplorerChoiceOption(
        id='name',
        label='По названию',
        description='Алфавитная сортировка без клиентской логики.',
    ),
}

TRANSPORT_OPTIONS = {
    'car': ExplorerTransportOption(
        id='car',
        label='Авто',
        accent='#ff7b37',
        description='Маршрут по автомобильной сети, с пешим добором при необходимости.',
    ),
    'bike': ExplorerTransportOption(
        id='bike',
        label='Вело',
        accent='#6de2a6',
        description='Маршрут по вело-проходимой сети, с переходом на walking-сегменты если нужно.',
    ),
    'foot': ExplorerTransportOption(
        id='foot',
        label='Пешком',
        accent='#ffd98a',
        description='Маршрут по walking-сети и безопасным off-network отрезкам.',
    ),
}

MARKER_PRESETS = {
    'petroglyph': ExplorerMarkerPresentation(kind='petroglyph', accent='#f4c95d', icon_key='sun'),
    'sacred_site': ExplorerMarkerPresentation(kind='sacred_site', accent='#ff7b37', icon_key='flame'),
    'calendar_event': ExplorerMarkerPresentation(kind='calendar_event', accent='#ffe36c', icon_key='moon'),
}

MODE_STYLES = {
    'car': {'solid': '#ff7b37', 'connector': '#ffd6b8', 'shadow': 'rgba(18, 10, 8, 0.86)'},
    'bike': {'solid': '#69dfa4', 'connector': '#c9f9df', 'shadow': 'rgba(7, 22, 15, 0.82)'},
    'foot': {'solid': '#ffe08a', 'connector': '#fff0c2', 'shadow': 'rgba(37, 29, 12, 0.84)'},
}


def _theme_definitions() -> list[ExplorerMapThemeDefinition]:
    if settings.MAPBOX_ACCESS_TOKEN:
        return [
            ExplorerMapThemeDefinition(
                id='night',
                label='Ночь',
                description='Навигационная ночная карта Mapbox.',
                tile_url=(
                    'https://api.mapbox.com/styles/v1/mapbox/navigation-night-v1/tiles/512/{z}/{x}/{y}@2x'
                    f'?access_token={settings.MAPBOX_ACCESS_TOKEN}'
                ),
                attribution=(
                    '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noreferrer">Mapbox</a> '
                    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>'
                ),
                tile_size=512,
                zoom_offset=-1,
                max_zoom=20,
                requires_token=True,
            ),
            ExplorerMapThemeDefinition(
                id='dawn',
                label='Рассвет',
                description='Навигационная дневная карта Mapbox.',
                tile_url=(
                    'https://api.mapbox.com/styles/v1/mapbox/navigation-day-v1/tiles/512/{z}/{x}/{y}@2x'
                    f'?access_token={settings.MAPBOX_ACCESS_TOKEN}'
                ),
                attribution=(
                    '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noreferrer">Mapbox</a> '
                    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>'
                ),
                tile_size=512,
                zoom_offset=-1,
                max_zoom=20,
                requires_token=True,
            ),
        ]

    return [
        ExplorerMapThemeDefinition(
            id='night',
            label='Ночь',
            description='Тёмный fallback-стиль на CARTO.',
            tile_url='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            attribution=(
                '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> '
                '&copy; <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">CARTO</a>'
            ),
            max_zoom=19,
        ),
        ExplorerMapThemeDefinition(
            id='dawn',
            label='Рассвет',
            description='Светлый fallback-стиль на CARTO.',
            tile_url='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
            attribution=(
                '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> '
                '&copy; <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">CARTO</a>'
            ),
            max_zoom=19,
        ),
    ]


def build_bootstrap_response() -> ExplorerBootstrapResponse:
    generic_segment_presets = [
        ExplorerRouteLegendItem(
            id='network',
            title='Основной участок',
            description='Сплошная линия по доступной дорожной или walking-сети.',
            stroke_color='#ff7b37',
            outline_color='rgba(18, 10, 8, 0.86)',
            weight=7,
        ),
        ExplorerRouteLegendItem(
            id='walk_connector',
            title='Пеший добор',
            description='Пунктирный или переходный участок, где маршрут продолжается пешком.',
            stroke_color='#ffd6b8',
            outline_color='rgba(18, 10, 8, 0.86)',
            dash_pattern='12 10',
            weight=5,
        ),
        ExplorerRouteLegendItem(
            id='approximation',
            title='Оценочная линия',
            description='Fallback при недоступности road network сервиса.',
            stroke_color='#f7efe3',
            outline_color='rgba(12, 10, 10, 0.78)',
            dash_pattern='12 14',
            weight=5,
        ),
    ]

    return ExplorerBootstrapResponse(
        app_name=settings.APP_NAME,
        defaults=ExplorerClientDefaults(),
        voice=ExplorerVoiceConfig(),
        map=ExplorerMapConfig(
            default_center=DEFAULT_CENTER,
            default_zoom=8,
            themes=_theme_definitions(),
        ),
        kinds=list(KIND_OPTIONS.values()),
        terrains=list(TERRAIN_OPTIONS.values()),
        sort_modes=list(SORT_OPTIONS.values()),
        transports=list(TRANSPORT_OPTIONS.values()),
        markers=list(MARKER_PRESETS.values()),
        route_rendering=ExplorerRouteRenderingConfig(segment_presets=generic_segment_presets),
    )


def build_media_asset(
    *,
    kind: LocationKind,
    image_url: str | None,
    gallery: list[str] | None = None,
) -> ExplorerMediaAsset:
    gallery_items = list(gallery or [])
    if image_url and image_url not in gallery_items:
        gallery_items = [image_url, *gallery_items]

    placeholder_tone = 'stone'
    if kind == 'sacred_site':
        placeholder_tone = 'ember'
    elif kind == 'calendar_event':
        placeholder_tone = 'sun'

    return ExplorerMediaAsset(
        hero_image_url=image_url,
        thumbnail_url=image_url,
        gallery=gallery_items,
        gallery_count=len(gallery_items),
        has_gallery=bool(gallery_items),
        placeholder_tone=placeholder_tone,  # type: ignore[arg-type]
    )


def build_marker_preset(kind: LocationKind) -> ExplorerMarkerPresentation:
    return MARKER_PRESETS.get(kind, MARKER_PRESETS['petroglyph'])


def build_location_badges(
    *,
    featured: bool,
    route_available: bool,
    coordinate_quality: str,
) -> list[str]:
    badges: list[str] = []
    if featured:
        badges.append('featured')
    if route_available:
        badges.append('route_ready')
    if coordinate_quality == 'verified':
        badges.append('verified')
    elif coordinate_quality == 'approximate':
        badges.append('approximate')
    return badges


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius_m * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _coordinate_path_distance_m(coordinates: list[list[float]]) -> float:
    if len(coordinates) < 2:
        return 0.0

    total = 0.0
    for current, nxt in zip(coordinates, coordinates[1:], strict=False):
        total += haversine_distance_m(current[1], current[0], nxt[1], nxt[0])
    return total


def distance_from_user(
    *,
    user_lat: float | None,
    user_lon: float | None,
    target_lat: float | None,
    target_lon: float | None,
) -> float | None:
    if None in {user_lat, user_lon, target_lat, target_lon}:
        return None
    return round(haversine_distance_m(user_lat, user_lon, target_lat, target_lon), 1)


def _segment_style(kind: str, context: str) -> dict[str, Any]:
    palette = MODE_STYLES.get(context, MODE_STYLES['car'])

    if kind == 'approximation':
        return {
            'stroke_color': '#f7efe3',
            'outline_color': 'rgba(12, 10, 10, 0.78)',
            'dash_pattern': '12 14',
            'weight': 5,
            'opacity': 0.82,
        }

    if kind == 'walk_connector':
        if context == 'foot':
            return {
                'stroke_color': palette['solid'],
                'outline_color': palette['shadow'],
                'dash_pattern': None,
                'weight': 6,
                'opacity': 0.98,
            }
        return {
            'stroke_color': palette['connector'],
            'outline_color': palette['shadow'],
            'dash_pattern': '12 10' if context == 'car' else '7 9' if context == 'bike' else '4 8',
            'weight': 5,
            'opacity': 0.96,
        }

    return {
        'stroke_color': palette['solid'],
        'outline_color': palette['shadow'],
        'dash_pattern': None,
        'weight': 7,
        'opacity': 0.98,
    }


def build_render_segments(
    *,
    route_geometry: dict[str, Any] | None,
    transport_mode: TransportMode,
) -> list[ExplorerRenderSegment]:
    explicit_segments = (route_geometry or {}).get('properties', {}).get('render_segments')
    raw_segments: list[dict[str, Any]]

    if isinstance(explicit_segments, list) and explicit_segments:
        raw_segments = [segment for segment in explicit_segments if isinstance(segment, dict)]
    else:
        coordinates = (route_geometry or {}).get('geometry', {}).get('coordinates') or []
        raw_segments = []
        if len(coordinates) > 1:
            raw_segments.append(
                {
                    'id': 'route-fallback',
                    'kind': 'approximation' if (route_geometry or {}).get('properties', {}).get('source') == 'fallback' else 'network',
                    'mode': transport_mode,
                    'transport_context': transport_mode,
                    'dashed': (route_geometry or {}).get('properties', {}).get('source') == 'fallback',
                    'label': 'Оценочная линия'
                    if (route_geometry or {}).get('properties', {}).get('source') == 'fallback'
                    else 'Маршрут по сети',
                    'coordinates': coordinates,
                }
            )

    segments: list[ExplorerRenderSegment] = []
    for index, segment in enumerate(raw_segments):
        coordinates = [list(item) for item in segment.get('coordinates') or [] if isinstance(item, list) and len(item) >= 2]
        if len(coordinates) < 2:
            continue

        context = segment.get('transport_context') or segment.get('mode') or transport_mode
        kind = segment.get('kind') or 'network'
        style = _segment_style(kind, context)
        segments.append(
            ExplorerRenderSegment(
                id=str(segment.get('id') or f'{kind}-{context}-{index}'),
                kind=kind,
                mode=segment.get('mode') or transport_mode,
                transport_context=context,
                label=segment.get('label'),
                source=segment.get('source'),
                dashed=bool(segment.get('dashed')),
                distance_m=round(float(segment.get('distance_m') or _coordinate_path_distance_m(coordinates)), 1),
                duration_s=round(float(segment.get('duration_s') or 0), 1),
                coordinates=coordinates,
                stroke_color=style['stroke_color'],
                outline_color=style['outline_color'],
                dash_pattern=style['dash_pattern'],
                weight=style['weight'],
                opacity=style['opacity'],
            )
        )
    return segments


def _legend_copy(locale: LocaleCode) -> dict[str, dict[str, str]]:
    if locale == 'ky':
        return {
            'network': {
                'title': 'Негизги бөлүк',
                'description': 'Жеткиликтүү жол же walking-сеть боюнча негизги маршрут.',
            },
            'walk_connector': {
                'title': 'Жөө өтмөк',
                'description': 'Маршруттун жүрбөгөн бөлүгү жөө улантылат.',
            },
            'approximation': {
                'title': 'Болжол сызык',
                'description': 'Роутинг сервис жетпей калганда fallback сызыгы.',
            },
        }

    if locale == 'en':
        return {
            'network': {
                'title': 'Primary segment',
                'description': 'Main route along the available road or walking network.',
            },
            'walk_connector': {
                'title': 'Walking connector',
                'description': 'A connector segment that must continue on foot.',
            },
            'approximation': {
                'title': 'Approximation',
                'description': 'Fallback line when road-network routing is unavailable.',
            },
        }

    return {
        'network': {
            'title': 'Основной участок',
            'description': 'Основной путь по доступной дороге, тропе или walking-сети.',
        },
        'walk_connector': {
            'title': 'Пеший добор',
            'description': 'Участок, где маршрут нужно продолжить пешком.',
        },
        'approximation': {
            'title': 'Оценочная линия',
            'description': 'Fallback-линия при недоступности road network.',
        },
    }


def build_route_legend(
    *,
    transport_mode: TransportMode,
    locale: LocaleCode,
    render_segments: list[ExplorerRenderSegment],
) -> list[ExplorerRouteLegendItem]:
    copy = _legend_copy(locale)
    seen: set[str] = set()
    legend: list[ExplorerRouteLegendItem] = []

    for segment in render_segments:
        if segment.kind in seen:
            continue
        seen.add(segment.kind)
        copy_item = copy.get(segment.kind, copy['network'])
        legend.append(
            ExplorerRouteLegendItem(
                id=segment.kind,
                title=copy_item['title'],
                description=copy_item['description'],
                stroke_color=segment.stroke_color,
                outline_color=segment.outline_color,
                dash_pattern=segment.dash_pattern,
                weight=segment.weight,
            )
        )

    if not legend:
        fallback_style = _segment_style('network', transport_mode)
        legend.append(
            ExplorerRouteLegendItem(
                id='network',
                title=copy['network']['title'],
                description=copy['network']['description'],
                stroke_color=fallback_style['stroke_color'],
                outline_color=fallback_style['outline_color'],
                weight=fallback_style['weight'],
            )
        )

    return legend


def build_viewport(
    *,
    route_geometry: dict[str, Any] | None,
    render_segments: list[ExplorerRenderSegment],
    selected_lat: float | None,
    selected_lon: float | None,
    user_lat: float,
    user_lon: float,
) -> ExplorerMapViewport:
    route_coordinates = []
    raw_coordinates = (route_geometry or {}).get('geometry', {}).get('coordinates') or []
    if len(raw_coordinates) > 1:
        route_coordinates = [[item[1], item[0]] for item in raw_coordinates if isinstance(item, list) and len(item) >= 2]
    elif render_segments:
        for segment in render_segments:
            route_coordinates.extend([[lon_lat[1], lon_lat[0]] for lon_lat in segment.coordinates])

    if len(route_coordinates) > 1:
        lats = [item[0] for item in route_coordinates]
        lons = [item[1] for item in route_coordinates]
        center = [round((min(lats) + max(lats)) / 2, 6), round((min(lons) + max(lons)) / 2, 6)]
        bounds = [
            [round(min(lats), 6), round(min(lons), 6)],
            [round(max(lats), 6), round(max(lons), 6)],
        ]
        return ExplorerMapViewport(
            mode='fit_route',
            center=center,
            bounds=bounds,
            zoom=13,
            mobile_zoom=10,
            desktop_zoom=11,
            max_zoom=13,
        )

    if selected_lat is not None and selected_lon is not None:
        center = [round(selected_lat, 6), round(selected_lon, 6)]
        return ExplorerMapViewport(
            mode='focus_destination',
            center=center,
            zoom=10,
            mobile_zoom=10,
            desktop_zoom=11,
        )

    return ExplorerMapViewport(
        mode='focus_user',
        center=[round(user_lat, 6), round(user_lon, 6)],
        zoom=8,
    )


def build_voice_guidance(
    *,
    text: str,
    locale: LocaleCode,
) -> ExplorerVoiceGuidance:
    return ExplorerVoiceGuidance(text=text, locale=locale)

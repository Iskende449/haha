import logging
import math
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

HTTP_CLIENT_HEADERS = {
    'User-Agent': 'NomadHeritage/1.0 (+https://nomad.local)',
}

PROFILE_MAP = {
    'car': {
        'mapbox': 'mapbox/driving-traffic',
        'ors': 'driving-car',
        'osrm': 'driving',
    },
    'bike': {
        'mapbox': 'mapbox/cycling',
        'ors': 'cycling-regular',
        'osrm': 'cycling',
    },
    'foot': {
        'mapbox': 'mapbox/walking',
        'ors': 'foot-walking',
        'osrm': 'walking',
    },
}

AVERAGE_SPEED_KMH = {
    'car': 52,
    'bike': 17,
    'foot': 4.8,
}

CONNECTOR_VISIBILITY_THRESHOLD_M = {
    'car': 20,
    'bike': 16,
    'foot': 12,
}

SMART_OFF_NETWORK_THRESHOLD_M = {
    'car': 20,
    'bike': 18,
    'foot': 14,
}

SPECIAL_OSRM_ENDPOINTS = {
    'bike': {
        'base_url': 'https://routing.openstreetmap.de/routed-bike',
        'route_profile': 'driving',
    },
    'foot': {
        'base_url': 'https://routing.openstreetmap.de/routed-foot',
        'route_profile': 'driving',
    },
}

BISHKEK_COORDS = (42.8746, 74.6122)

COPY = {
    'ru': {
        'traffic': {
            'low': 'дороги свободны',
            'medium': 'есть умеренные пробки',
            'high': 'трафик плотный',
        },
        'style': {
            'smart': 'продуманный маршрут',
        },
        'transport': {
            'car': 'на машине',
            'bike': 'на велосипеде',
            'foot': 'пешком',
        },
        'analysis': (
            'AI собрал {style_label} до {location}. Длина маршрута {distance_km} км, время в пути около {eta_minutes} мин. '
            'По трафику сейчас {traffic_label}, задержка около {delay_minutes} мин.'
        ),
        'analysis_mode': (
            'AI собрал {style_label} до {location}. Длина маршрута {distance_km} км, время в пути около {eta_minutes} мин. '
            'Маршрут рассчитан отдельно для режима {transport_label}.'
        ),
        'voice': (
            'Маршрут до {location} готов. Едем {transport_label}. {traffic_sentence} '
            'Первый маневр: {first_step}.'
        ),
        'voice_no_steps': (
            'Маршрут до {location} готов. Едем {transport_label}. {traffic_sentence}'
        ),
        'traffic_sentence': {
            'low': 'Путь спокойный, серьёзных пробок нет.',
            'medium': 'Есть средняя нагрузка на дороге, я уже учёл это в ETA.',
            'high': 'Есть плотный трафик, поэтому время скорректировано по живым данным.',
        },
    },
    'en': {
        'traffic': {
            'low': 'roads are flowing',
            'medium': 'traffic is moderate',
            'high': 'traffic is heavy',
        },
        'style': {
            'smart': 'thought-out route',
        },
        'transport': {
            'car': 'by car',
            'bike': 'by bike',
            'foot': 'on foot',
        },
        'analysis': (
            'AI built a {style_label} to {location}. Total distance is {distance_km} km and travel time is about {eta_minutes} min. '
            'Right now {traffic_label}, with roughly {delay_minutes} extra min from traffic.'
        ),
        'analysis_mode': (
            'AI built a {style_label} to {location}. Total distance is {distance_km} km and travel time is about {eta_minutes} min. '
            'The route is calculated specifically for traveling {transport_label}.'
        ),
        'voice': (
            'Your route to {location} is ready. We are going {transport_label}. {traffic_sentence} '
            'First move: {first_step}.'
        ),
        'voice_no_steps': (
            'Your route to {location} is ready. We are going {transport_label}. {traffic_sentence}'
        ),
        'traffic_sentence': {
            'low': 'The road looks calm with no major slowdowns.',
            'medium': 'There is moderate traffic, and I already included it in the ETA.',
            'high': 'Traffic is heavy, so the ETA is adjusted using live road data.',
        },
    },
    'ky': {
        'traffic': {
            'low': 'жол ачык',
            'medium': 'тыгыздык орточо',
            'high': 'жол тыгыны күчтүү',
        },
        'style': {
            'smart': 'ойлонулган маршрут',
        },
        'transport': {
            'car': 'унаа менен',
            'bike': 'велосипед менен',
            'foot': 'жөө',
        },
        'analysis': (
            'AI {location} тарапка {style_label} түздү. Узундугу {distance_km} км, убактысы болжол {eta_minutes} мүнөт. '
            'Азыр {traffic_label}, кечигүү болжол {delay_minutes} мүнөт.'
        ),
        'analysis_mode': (
            'AI {location} тарапка {style_label} түздү. Узундугу {distance_km} км, убактысы болжол {eta_minutes} мүнөт. '
            'Маршрут {transport_label} режими үчүн өзүнчө эсептелди.'
        ),
        'voice': (
            '{location} багыты даяр. Жол {transport_label}. {traffic_sentence} '
            'Биринчи аракет: {first_step}.'
        ),
        'voice_no_steps': (
            '{location} багыты даяр. Жол {transport_label}. {traffic_sentence}'
        ),
        'traffic_sentence': {
            'low': 'Жол тынч, чоң тыгын жок.',
            'medium': 'Орточо тыгын бар, мен ETAга кошуп бердим.',
            'high': 'Жол тыгыны күчтүү, убакыт жандуу маалымат менен жаңыртылды.',
        },
    },
}


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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


def _estimated_duration_s(distance_m: float, transport_type: str) -> float:
    speed_kmh = AVERAGE_SPEED_KMH.get(transport_type, 52)
    return distance_m / (speed_kmh * 1000 / 3600)


def _distance_to_bishkek_km(lat: float, lon: float) -> float:
    return _haversine_distance_m(lat, lon, BISHKEK_COORDS[0], BISHKEK_COORDS[1]) / 1000


def _mapbox_language(locale: str) -> str:
    return {
        'ru': 'ru',
        'en': 'en',
        'ky': 'ru',
    }.get(locale, 'en')


def _copy(locale: str) -> dict[str, Any]:
    return COPY.get(locale, COPY['en'])


def _format_distance_label(distance_m: float, locale: str) -> str:
    if distance_m >= 1000:
        value = round(distance_m / 100) / 10
        unit = 'км' if locale in {'ru', 'ky'} else 'km'
        return f'{value:.1f} {unit}'
    unit = 'м' if locale in {'ru', 'ky'} else 'm'
    return f'{round(distance_m)} {unit}'


def _route_mode_label(locale: str, transport_type: str) -> str:
    copy = _copy(locale)
    return copy['transport'].get(transport_type, copy['transport']['car'])


def _fallback_geometry(
    *,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    profile: str,
    source: str,
    transport_type: str,
) -> dict[str, Any]:
    coordinates = [[start_lon, start_lat], [end_lon, end_lat]]
    segment = _build_render_segment(
        coordinates=coordinates,
        mode=transport_type,
        kind='approximation',
        dashed=True,
        label='Approximate line',
        source=source,
        transport_context=transport_type,
    )
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': coordinates,
        },
        'properties': {
            'source': source,
            'profile': profile,
            'segment_congestion': [],
            'segment_congestion_numeric': [],
            'segment_duration': [],
            'segment_distance': [],
            'alternatives_count': 0,
            'render_segments': [segment],
            'connector_summary': _empty_connector_summary(),
        },
    }


def _primary_voice_instruction(step: dict[str, Any]) -> str | None:
    voice_instructions = step.get('voiceInstructions') or step.get('voice_instructions') or []
    if voice_instructions:
        return voice_instructions[0].get('announcement')
    return None


def _instruction_suffix(name: str | None) -> str:
    if not name:
        return ''
    cleaned = name.strip()
    return f' on {cleaned}' if cleaned else ''


def _build_step_payload(route: dict[str, Any]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for leg in route.get('legs', []):
        for step in leg.get('steps', []):
            maneuver = step.get('maneuver', {})
            location = maneuver.get('location') or [None, None]
            instruction = maneuver.get('instruction') or step.get('name') or f'Continue{_instruction_suffix(step.get("ref"))}'
            payload.append(
                {
                    'instruction': instruction,
                    'distance_m': float(step.get('distance', 0)),
                    'duration_s': float(step.get('duration', 0)),
                    'maneuver_type': maneuver.get('type', 'continue'),
                    'modifier': maneuver.get('modifier'),
                    'latitude': location[1],
                    'longitude': location[0],
                    'voice_announcement': _primary_voice_instruction(step),
                }
            )
    return payload


def _route_reference_suffix(name: str | None, locale: str) -> str:
    if not name:
        return ''
    cleaned = name.strip()
    if not cleaned:
        return ''
    if locale == 'ru':
        return f' на {cleaned}'
    if locale == 'ky':
        return f' {cleaned} аркылуу'
    return f' onto {cleaned}'


def _osrm_modifier_label(modifier: str | None, locale: str) -> str:
    copy_map = {
        'ru': {
            'left': 'налево',
            'right': 'направо',
            'slight left': 'слегка налево',
            'slight right': 'слегка направо',
            'sharp left': 'резко налево',
            'sharp right': 'резко направо',
            'straight': 'прямо',
            'uturn': 'развернитесь',
        },
        'ky': {
            'left': 'солго',
            'right': 'оңго',
            'slight left': 'бир аз солго',
            'slight right': 'бир аз оңго',
            'sharp left': 'кескин солго',
            'sharp right': 'кескин оңго',
            'straight': 'түз',
            'uturn': 'кайра бурулуңуз',
        },
        'en': {
            'left': 'left',
            'right': 'right',
            'slight left': 'slight left',
            'slight right': 'slight right',
            'sharp left': 'sharp left',
            'sharp right': 'sharp right',
            'straight': 'straight',
            'uturn': 'make a U-turn',
        },
    }
    locale_copy = copy_map.get(locale, copy_map['en'])
    return locale_copy.get(modifier or '', modifier or '')


def _build_osrm_instruction(step: dict[str, Any], locale: str) -> str:
    maneuver = step.get('maneuver') or {}
    maneuver_type = maneuver.get('type', 'continue')
    modifier = maneuver.get('modifier')
    road_suffix = _route_reference_suffix(step.get('name') or step.get('ref'), locale)
    direction = _osrm_modifier_label(modifier, locale)

    if locale == 'ru':
        if maneuver_type == 'depart':
            return f'Начните движение{road_suffix}'.strip()
        if maneuver_type == 'arrive':
            return 'Прибытие к точке назначения'
        if maneuver_type in {'roundabout', 'rotary'}:
            return f'На круге держитесь {direction or "по ходу движения"}{road_suffix}'.strip()
        if maneuver_type in {'on ramp', 'merge'}:
            return f'Влейтесь {direction or "по направлению потока"}{road_suffix}'.strip()
        if maneuver_type == 'off ramp':
            return f'Съезжайте {direction or "по указателю"}{road_suffix}'.strip()
        if maneuver_type in {'fork', 'end of road'}:
            return f'Держитесь {direction or "по основному направлению"}{road_suffix}'.strip()
        if maneuver_type == 'continue':
            return f'Продолжайте {direction or "движение прямо"}{road_suffix}'.strip()
        if maneuver_type == 'new name':
            return f'Продолжайте по дороге{road_suffix}'.strip()
        if maneuver_type == 'turn':
            return f'Поверните {direction or "по направлению"}{road_suffix}'.strip()
        return f'Продолжайте движение{road_suffix}'.strip()

    if locale == 'ky':
        if maneuver_type == 'depart':
            return f'Жолду баштаңыз{road_suffix}'.strip()
        if maneuver_type == 'arrive':
            return 'Белгиленген чекитке жеттиңиз'
        if maneuver_type in {'roundabout', 'rotary'}:
            return f'Айланмада {direction or "белгиленген багытты"} кармаңыз{road_suffix}'.strip()
        if maneuver_type in {'on ramp', 'merge'}:
            return f'Агымга кошулуңуз{road_suffix}'.strip()
        if maneuver_type == 'off ramp':
            return f'Бурулуштан чыгыңыз{road_suffix}'.strip()
        if maneuver_type in {'fork', 'end of road'}:
            return f'{direction or "негизги багытты"} кармаңыз{road_suffix}'.strip()
        if maneuver_type == 'turn':
            return f'{direction or "багыт боюнча"} бурулуңуз{road_suffix}'.strip()
        if maneuver_type == 'new name':
            return f'Ушул жол менен улантыңыз{road_suffix}'.strip()
        return f'Түз улантыңыз{road_suffix}'.strip()

    if maneuver_type == 'depart':
        return f'Start moving{road_suffix}'.strip()
    if maneuver_type == 'arrive':
        return 'Arrive at the destination'
    if maneuver_type in {'roundabout', 'rotary'}:
        return f'At the roundabout keep {direction or "following the route"}{road_suffix}'.strip()
    if maneuver_type in {'on ramp', 'merge'}:
        return f'Merge {direction or "with traffic"}{road_suffix}'.strip()
    if maneuver_type == 'off ramp':
        return f'Take the exit {direction or "as signed"}{road_suffix}'.strip()
    if maneuver_type in {'fork', 'end of road'}:
        return f'Keep {direction or "along the main direction"}{road_suffix}'.strip()
    if maneuver_type == 'new name':
        return f'Continue on the road{road_suffix}'.strip()
    if maneuver_type == 'turn':
        return f'Turn {direction or "as directed"}{road_suffix}'.strip()
    return f'Continue{road_suffix}'.strip()


def _build_osrm_steps(route: dict[str, Any], locale: str) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for leg in route.get('legs', []):
        for step in leg.get('steps', []):
            maneuver = step.get('maneuver') or {}
            location = maneuver.get('location') or [None, None]
            instruction = _build_osrm_instruction(step, locale)
            payload.append(
                {
                    'instruction': instruction,
                    'distance_m': float(step.get('distance', 0)),
                    'duration_s': float(step.get('duration', 0)),
                    'maneuver_type': maneuver.get('type', 'continue'),
                    'modifier': maneuver.get('modifier'),
                    'latitude': location[1],
                    'longitude': location[0],
                    'voice_announcement': instruction,
                }
            )
    return payload


def _coordinate_path_distance_m(coordinates: list[list[float]]) -> float:
    if len(coordinates) < 2:
        return 0.0
    total = 0.0
    for index in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[index]
        lon2, lat2 = coordinates[index + 1]
        total += _haversine_distance_m(lat1, lon1, lat2, lon2)
    return total


def _build_render_segment(
    *,
    coordinates: list[list[float]],
    mode: str,
    kind: str,
    dashed: bool,
    label: str,
    source: str,
    distance_m: float | None = None,
    duration_s: float | None = None,
    transport_context: str | None = None,
) -> dict[str, Any]:
    resolved_distance_m = distance_m if distance_m is not None else _coordinate_path_distance_m(coordinates)
    resolved_mode = mode if mode in AVERAGE_SPEED_KMH else 'foot'
    resolved_duration_s = (
        duration_s
        if duration_s is not None
        else _estimated_duration_s(resolved_distance_m, resolved_mode)
    )
    return {
        'kind': kind,
        'mode': mode,
        'dashed': dashed,
        'label': label,
        'source': source,
        'transport_context': transport_context or mode,
        'distance_m': round(resolved_distance_m, 1),
        'duration_s': round(resolved_duration_s, 1),
        'coordinates': coordinates,
    }


def _merge_segment_coordinates(segments: list[dict[str, Any]]) -> list[list[float]]:
    merged: list[list[float]] = []
    for segment in segments:
        coordinates = segment.get('coordinates') or []
        if not coordinates:
            continue
        if not merged:
            merged.extend(coordinates)
            continue
        if merged[-1] == coordinates[0]:
            merged.extend(coordinates[1:])
            continue
        merged.extend(coordinates)
    return merged


def _empty_connector_summary() -> dict[str, Any]:
    return {
        'has_walk_connector': False,
        'start_walk_distance_m': 0.0,
        'end_walk_distance_m': 0.0,
        'walk_distance_m': 0.0,
    }


def _connector_instruction(
    *,
    locale: str,
    transport_type: str,
    phase: str,
    distance_m: float,
) -> str:
    distance_label = _format_distance_label(distance_m, locale)
    if locale == 'ru':
        if phase == 'start':
            if transport_type == 'car':
                return f'Дойдите пешком {distance_label} до ближайшей дороги, где можно продолжить на машине.'
            if transport_type == 'bike':
                return f'Пройдите {distance_label} до участка, где можно продолжить маршрут на велосипеде.'
            return f'Пройдите {distance_label} до начала доступной тропы.'
        if transport_type == 'car':
            return f'После окончания проезда пройдите пешком последние {distance_label} до точки.'
        if transport_type == 'bike':
            return f'После участка для велосипеда пройдите пешком последние {distance_label} до точки.'
        return f'Последние {distance_label} пройдите по местности пешком до точки.'

    if locale == 'ky':
        if phase == 'start':
            if transport_type == 'car':
                return f'Унаа жүрө турган жолго чейин {distance_label} жөө өтүңүз.'
            if transport_type == 'bike':
                return f'Велосипед менен өтө турган бөлүккө чейин {distance_label} жөө өтүңүз.'
            return f'Жеткиликтүү тропага чейин {distance_label} басыңыз.'
        if transport_type == 'car':
            return f'Жол бүткөндөн кийин чекитке чейин акыркы {distance_label} жөө өтүңүз.'
        if transport_type == 'bike':
            return f'Велосипед жолу бүткөндөн кийин акыркы {distance_label} жөө өтүңүз.'
        return f'Акыркы {distance_label} чекитке чейин жөө өтүңүз.'

    if phase == 'start':
        if transport_type == 'car':
            return f'Walk {distance_label} to the nearest road where the car route can begin.'
        if transport_type == 'bike':
            return f'Walk {distance_label} to the nearest segment where the bike route can begin.'
        return f'Walk {distance_label} to the nearest mapped path.'
    if transport_type == 'car':
        return f'After the drivable road ends, walk the final {distance_label} to the destination.'
    if transport_type == 'bike':
        return f'After the bike-accessible section ends, walk the final {distance_label} to the destination.'
    return f'Walk the final {distance_label} to the destination.'


def _build_connector_step(
    *,
    locale: str,
    transport_type: str,
    phase: str,
    distance_m: float,
    coordinate: list[float],
) -> dict[str, Any]:
    instruction = _connector_instruction(
        locale=locale,
        transport_type=transport_type,
        phase=phase,
        distance_m=distance_m,
    )
    return {
        'instruction': instruction,
        'distance_m': round(distance_m, 1),
        'duration_s': round(_estimated_duration_s(distance_m, 'foot'), 1),
        'maneuver_type': 'walk_connector',
        'modifier': phase,
        'latitude': coordinate[1],
        'longitude': coordinate[0],
        'voice_announcement': instruction,
    }


def _route_segments_from_geometry(
    geometry: dict[str, Any] | None,
    *,
    transport_type: str,
    source: str,
    label: str | None = None,
    dashed: bool = False,
) -> list[dict[str, Any]]:
    coordinates = (geometry or {}).get('coordinates') or []
    if len(coordinates) < 2:
        return []
    return [
        _build_render_segment(
            coordinates=coordinates,
            mode=transport_type,
            kind='network' if not dashed else 'approximation',
            dashed=dashed,
            label=label or 'Network route',
            source=source,
            transport_context=transport_type,
        )
    ]


def _collect_route_annotations(route: dict[str, Any]) -> dict[str, list[Any]]:
    summary = {'distance': [], 'duration': [], 'speed': []}
    for leg in route.get('legs', []):
        annotation = leg.get('annotation') or {}
        for key in summary:
            summary[key].extend(annotation.get(key, []))
    return summary


async def _get_mapbox_route_data(
    *,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    transport_type: str,
    locale: str,
    route_style: str,
) -> dict[str, Any]:
    profile = PROFILE_MAP.get(transport_type, PROFILE_MAP['car'])['mapbox']
    coordinates = f'{start_lon},{start_lat};{end_lon},{end_lat}'
    params = {
        'alternatives': 'false',
        'geometries': 'geojson',
        'overview': 'full',
        'steps': 'true',
        'banner_instructions': 'true',
        'voice_instructions': 'true',
        'roundabout_exits': 'true',
        'language': _mapbox_language(locale),
        'annotations': 'distance,duration,speed',
        'access_token': settings.MAPBOX_ACCESS_TOKEN,
    }

    if transport_type == 'car':
        params['annotations'] = 'distance,duration,speed,congestion,congestion_numeric,maxspeed,closure'
        params['depart_at'] = datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    url = f'https://api.mapbox.com/directions/v5/{profile}/{coordinates}'
    async with httpx.AsyncClient(timeout=settings.MAPBOX_TIMEOUT, headers=HTTP_CLIENT_HEADERS) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    routes = data.get('routes') or []
    if not routes:
        raise ValueError('Mapbox returned no routes')

    route = routes[0]
    leg = route.get('legs', [{}])[0]
    annotation = leg.get('annotation', {})
    geometry = route.get('geometry') or {
        'type': 'LineString',
        'coordinates': [[start_lon, start_lat], [end_lon, end_lat]],
    }
    render_segments = _route_segments_from_geometry(
        geometry,
        transport_type=transport_type,
        source='mapbox',
        label='Road route',
    )

    feature = {
        'type': 'Feature',
        'geometry': geometry,
        'properties': {
            'source': 'mapbox',
            'profile': profile,
            'segment_congestion': annotation.get('congestion', []),
            'segment_congestion_numeric': annotation.get('congestion_numeric', []),
            'segment_duration': annotation.get('duration', []),
            'segment_distance': annotation.get('distance', []),
            'alternatives_count': max(0, len(routes) - 1),
            'route_weight': route.get('weight'),
            'route_weight_typical': route.get('weight_typical'),
            'render_segments': render_segments,
            'connector_summary': _empty_connector_summary(),
        },
    }

    incidents_count = sum(len(item.get('incidents', [])) for item in route.get('legs', []))
    closures_count = sum(len(item.get('closures', [])) for item in route.get('legs', []))

    return {
        'geometry': feature,
        'distance_m': float(route.get('distance', 0)),
        'duration_s': float(route.get('duration', 0)),
        'typical_duration_s': float(route.get('duration_typical', route.get('duration', 0))),
        'provider': 'mapbox',
        'profile': profile,
        'steps': _build_step_payload(route),
        'alternatives_count': max(0, len(routes) - 1),
        'incident_count': incidents_count,
        'closure_count': closures_count,
        'connector_summary': _empty_connector_summary(),
    }


async def _get_ors_route_data(
    *,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    transport_type: str,
) -> dict[str, Any]:
    if not settings.ORS_API_KEY:
        raise ValueError('ORS API key is not configured')

    profile = PROFILE_MAP.get(transport_type, PROFILE_MAP['car'])['ors']
    straight_distance_m = _haversine_distance_m(start_lat, start_lon, end_lat, end_lon)
    url = f'https://api.openrouteservice.org/v2/directions/{profile}/geojson'
    payload = {'coordinates': [[start_lon, start_lat], [end_lon, end_lat]]}
    headers = {'Authorization': settings.ORS_API_KEY, 'Content-Type': 'application/json'}

    async with httpx.AsyncClient(timeout=settings.ORS_TIMEOUT, headers=HTTP_CLIENT_HEADERS) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    feature = data['features'][0]
    summary = feature.get('properties', {}).get('summary', {})
    feature.setdefault('properties', {})
    feature['properties'].update(
        {
            'source': 'openrouteservice',
            'segment_congestion': [],
            'segment_congestion_numeric': [],
            'segment_duration': [],
            'segment_distance': [],
            'alternatives_count': 0,
            'render_segments': _route_segments_from_geometry(
                feature.get('geometry'),
                transport_type=transport_type,
                source='openrouteservice',
                label='Road route',
            ),
            'connector_summary': _empty_connector_summary(),
        }
    )

    return {
        'geometry': feature,
        'distance_m': float(summary.get('distance', straight_distance_m)),
        'duration_s': float(summary.get('duration', _estimated_duration_s(straight_distance_m, transport_type))),
        'typical_duration_s': float(summary.get('duration', _estimated_duration_s(straight_distance_m, transport_type))),
        'provider': 'openrouteservice',
        'profile': profile,
        'steps': [],
        'alternatives_count': 0,
        'incident_count': 0,
        'closure_count': 0,
        'connector_summary': _empty_connector_summary(),
    }


def _normalize_osrm_waypoint(
    waypoint: dict[str, Any] | None,
    *,
    fallback_lon: float,
    fallback_lat: float,
) -> dict[str, Any]:
    location = (waypoint or {}).get('location') or [fallback_lon, fallback_lat]
    return {
        'location': [float(location[0]), float(location[1])],
        'distance_m': float((waypoint or {}).get('distance', 0) or 0),
        'name': (waypoint or {}).get('name'),
    }


async def _request_osrm_route(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    route_profile: str,
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    steps: bool = True,
) -> dict[str, Any]:
    url = f'{base_url}/route/v1/{route_profile}/{start_lon},{start_lat};{end_lon},{end_lat}'
    params = {
        'alternatives': 'false',
        'overview': 'full',
        'steps': 'true' if steps else 'false',
        'annotations': 'duration,distance,speed',
        'geometries': 'geojson',
    }
    response = await client.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    routes = data.get('routes') or []
    if not routes:
        raise ValueError(f'OSRM returned no routes for profile {route_profile}')

    waypoints = data.get('waypoints') or []
    start_waypoint = _normalize_osrm_waypoint(
        waypoints[0] if len(waypoints) > 0 else None,
        fallback_lon=start_lon,
        fallback_lat=start_lat,
    )
    end_waypoint = _normalize_osrm_waypoint(
        waypoints[1] if len(waypoints) > 1 else None,
        fallback_lon=end_lon,
        fallback_lat=end_lat,
    )

    return {
        'route': routes[0],
        'start_waypoint': start_waypoint,
        'end_waypoint': end_waypoint,
        'alternatives_count': max(0, len(routes) - 1),
    }


def _sum_segments(segments: list[dict[str, Any]]) -> tuple[float, float]:
    distance_m = sum(float(segment.get('distance_m', 0) or 0) for segment in segments)
    duration_s = sum(float(segment.get('duration_s', 0) or 0) for segment in segments)
    return round(distance_m, 1), round(duration_s, 1)


def _build_osrm_route_segment(
    *,
    route: dict[str, Any],
    mode: str,
    kind: str,
    dashed: bool,
    label: str,
    transport_context: str,
) -> dict[str, Any] | None:
    geometry = route.get('geometry') or {}
    coordinates = geometry.get('coordinates') or []
    if len(coordinates) < 2:
        return None
    return _build_render_segment(
        coordinates=coordinates,
        mode=mode,
        kind=kind,
        dashed=dashed,
        label=label,
        source='osrm',
        distance_m=float(route.get('distance', _coordinate_path_distance_m(coordinates))),
        duration_s=float(route.get('duration', _estimated_duration_s(_coordinate_path_distance_m(coordinates), mode))),
        transport_context=transport_context,
    )


def _build_direct_connector_segment(
    *,
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    transport_context: str,
    label: str,
    kind: str = 'walk_connector',
) -> dict[str, Any] | None:
    distance_m = _haversine_distance_m(start_lat, start_lon, end_lat, end_lon)
    if distance_m <= 1:
        return None
    return _build_render_segment(
        coordinates=[[start_lon, start_lat], [end_lon, end_lat]],
        mode='foot',
        kind=kind,
        dashed=True,
        label=label,
        source='osrm',
        distance_m=distance_m,
        duration_s=_estimated_duration_s(distance_m, 'foot'),
        transport_context=transport_context,
    )


def _waypoint_payload(waypoint: dict[str, Any]) -> dict[str, Any]:
    return {
        'location': waypoint['location'],
        'distance_m': round(float(waypoint.get('distance_m', 0) or 0), 1),
        'name': waypoint.get('name'),
    }


def _osrm_service_for_mode(transport_type: str) -> dict[str, str]:
    if transport_type in SPECIAL_OSRM_ENDPOINTS:
        return SPECIAL_OSRM_ENDPOINTS[transport_type]
    return {
        'base_url': settings.OSRM_BASE_URL.rstrip('/'),
        'route_profile': PROFILE_MAP.get(transport_type, PROFILE_MAP['car'])['osrm'],
    }


async def _build_walk_connector_path(
    *,
    client: httpx.AsyncClient,
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    transport_context: str,
    locale: str,
    phase: str,
) -> dict[str, Any]:
    segments: list[dict[str, Any]] = []
    foot_service = _osrm_service_for_mode('foot')
    fallback_segment = _build_direct_connector_segment(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
        transport_context=transport_context,
        label='Walking handoff',
    )

    try:
        walking_result = await _request_osrm_route(
            client=client,
            base_url=foot_service['base_url'],
            route_profile=foot_service['route_profile'],
            start_lon=start_lon,
            start_lat=start_lat,
            end_lon=end_lon,
            end_lat=end_lat,
            steps=False,
        )
    except Exception:  # noqa: BLE001
        walking_result = None

    if walking_result is None:
        if fallback_segment is not None:
            segments.append(fallback_segment)
    else:
        start_waypoint = walking_result['start_waypoint']
        end_waypoint = walking_result['end_waypoint']

        if start_waypoint['distance_m'] > SMART_OFF_NETWORK_THRESHOLD_M['foot']:
            initial_segment = _build_direct_connector_segment(
                start_lon=start_lon,
                start_lat=start_lat,
                end_lon=start_waypoint['location'][0],
                end_lat=start_waypoint['location'][1],
                transport_context=transport_context,
                label='Walk to the mapped path',
            )
            if initial_segment is not None:
                segments.append(initial_segment)

        walking_segment = _build_osrm_route_segment(
            route=walking_result['route'],
            mode='foot',
            kind='walk_connector',
            dashed=True,
            label='Walking handoff',
            transport_context=transport_context,
        )
        if walking_segment is not None:
            segments.append(walking_segment)

        if end_waypoint['distance_m'] > SMART_OFF_NETWORK_THRESHOLD_M['foot']:
            tail_segment = _build_direct_connector_segment(
                start_lon=end_waypoint['location'][0],
                start_lat=end_waypoint['location'][1],
                end_lon=end_lon,
                end_lat=end_lat,
                transport_context=transport_context,
                label='Last off-network traverse',
            )
            if tail_segment is not None:
                segments.append(tail_segment)

    connector_distance_m, connector_duration_s = _sum_segments(segments)
    summary_step = (
        _build_connector_step(
            locale=locale,
            transport_type=transport_context,
            phase=phase,
            distance_m=connector_distance_m,
            coordinate=[end_lon, end_lat],
        )
        if connector_distance_m > 0
        else None
    )

    return {
        'segments': segments,
        'distance_m': connector_distance_m,
        'duration_s': connector_duration_s,
        'summary_step': summary_step,
    }


def _build_osrm_feature(
    *,
    profile: str,
    route: dict[str, Any],
    render_segments: list[dict[str, Any]],
    start_waypoint: dict[str, Any],
    end_waypoint: dict[str, Any],
    connector_summary: dict[str, Any],
) -> dict[str, Any]:
    merged_coordinates = _merge_segment_coordinates(render_segments)
    if len(merged_coordinates) < 2:
        merged_coordinates = (route.get('geometry') or {}).get('coordinates') or merged_coordinates
    if len(merged_coordinates) < 2:
        merged_coordinates = [start_waypoint['location'], end_waypoint['location']]

    annotation = _collect_route_annotations(route)
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': merged_coordinates,
        },
        'properties': {
            'source': 'osrm',
            'profile': profile,
            'route_strategy': 'smart',
            'segment_congestion': [],
            'segment_congestion_numeric': [],
            'segment_duration': annotation.get('duration', []),
            'segment_distance': annotation.get('distance', []),
            'alternatives_count': 0,
            'render_segments': render_segments,
            'snapped_waypoints': {
                'start': _waypoint_payload(start_waypoint),
                'end': _waypoint_payload(end_waypoint),
            },
            'connector_summary': connector_summary,
        },
    }


async def _get_osrm_route_data(
    *,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    transport_type: str,
    locale: str,
    route_style: str,  # noqa: ARG001
) -> dict[str, Any]:
    service = _osrm_service_for_mode(transport_type)
    base_url = service['base_url'].rstrip('/')
    if not base_url:
        raise ValueError('OSRM base URL is not configured')

    profile = service['route_profile']
    threshold = CONNECTOR_VISIBILITY_THRESHOLD_M.get(transport_type, 15)

    async with httpx.AsyncClient(timeout=settings.OSRM_TIMEOUT, follow_redirects=True, headers=HTTP_CLIENT_HEADERS) as client:
        main_result = await _request_osrm_route(
            client=client,
            base_url=base_url,
            route_profile=profile,
            start_lon=start_lon,
            start_lat=start_lat,
            end_lon=end_lon,
            end_lat=end_lat,
            steps=True,
        )

        main_route = main_result['route']
        start_waypoint = main_result['start_waypoint']
        end_waypoint = main_result['end_waypoint']

        render_segments: list[dict[str, Any]] = []
        steps: list[dict[str, Any]] = []
        start_walk_distance_m = 0.0
        end_walk_distance_m = 0.0

        if transport_type in {'car', 'bike'} and start_waypoint['distance_m'] > threshold:
            start_connector = await _build_walk_connector_path(
                client=client,
                start_lon=start_lon,
                start_lat=start_lat,
                end_lon=start_waypoint['location'][0],
                end_lat=start_waypoint['location'][1],
                transport_context=transport_type,
                locale=locale,
                phase='start',
            )
            render_segments.extend(start_connector['segments'])
            start_walk_distance_m = start_connector['distance_m']
            if start_connector['summary_step'] is not None:
                steps.append(start_connector['summary_step'])
        elif transport_type == 'foot' and start_waypoint['distance_m'] > threshold:
            start_foot_segment = _build_direct_connector_segment(
                start_lon=start_lon,
                start_lat=start_lat,
                end_lon=start_waypoint['location'][0],
                end_lat=start_waypoint['location'][1],
                transport_context='foot',
                label='Walk to the first mapped path',
                kind='walk_connector',
            )
            if start_foot_segment is not None:
                render_segments.append(start_foot_segment)
                start_walk_distance_m = float(start_foot_segment['distance_m'])
                steps.append(
                    _build_connector_step(
                        locale=locale,
                        transport_type='foot',
                        phase='start',
                        distance_m=start_walk_distance_m,
                        coordinate=start_waypoint['location'],
                    )
                )

        main_segment = _build_osrm_route_segment(
            route=main_route,
            mode=transport_type,
            kind='network',
            dashed=False,
            label='Main network route',
            transport_context=transport_type,
        )
        if main_segment is not None:
            render_segments.append(main_segment)
        steps.extend(_build_osrm_steps(main_route, locale))

        if transport_type in {'car', 'bike'} and end_waypoint['distance_m'] > threshold:
            end_connector = await _build_walk_connector_path(
                client=client,
                start_lon=end_waypoint['location'][0],
                start_lat=end_waypoint['location'][1],
                end_lon=end_lon,
                end_lat=end_lat,
                transport_context=transport_type,
                locale=locale,
                phase='end',
            )
            render_segments.extend(end_connector['segments'])
            end_walk_distance_m = end_connector['distance_m']
            if end_connector['summary_step'] is not None:
                steps.append(end_connector['summary_step'])
        elif transport_type == 'foot' and end_waypoint['distance_m'] > threshold:
            end_foot_segment = _build_direct_connector_segment(
                start_lon=end_waypoint['location'][0],
                start_lat=end_waypoint['location'][1],
                end_lon=end_lon,
                end_lat=end_lat,
                transport_context='foot',
                label='Final off-network walking traverse',
                kind='walk_connector',
            )
            if end_foot_segment is not None:
                render_segments.append(end_foot_segment)
                end_walk_distance_m = float(end_foot_segment['distance_m'])
                steps.append(
                    _build_connector_step(
                        locale=locale,
                        transport_type='foot',
                        phase='end',
                        distance_m=end_walk_distance_m,
                        coordinate=[end_lon, end_lat],
                    )
                )

    total_distance_m, total_duration_s = _sum_segments(render_segments)
    connector_summary = {
        'has_walk_connector': (start_walk_distance_m + end_walk_distance_m) > 0,
        'start_walk_distance_m': round(start_walk_distance_m, 1),
        'end_walk_distance_m': round(end_walk_distance_m, 1),
        'walk_distance_m': round(start_walk_distance_m + end_walk_distance_m, 1),
    }

    feature = _build_osrm_feature(
        profile=profile,
        route=main_route,
        render_segments=render_segments,
        start_waypoint=start_waypoint,
        end_waypoint=end_waypoint,
        connector_summary=connector_summary,
    )

    return {
        'geometry': feature,
        'distance_m': total_distance_m or float(main_route.get('distance', 0)),
        'duration_s': total_duration_s or float(main_route.get('duration', 0)),
        'typical_duration_s': total_duration_s or float(main_route.get('duration', 0)),
        'provider': 'osrm',
        'profile': profile,
        'steps': steps,
        'alternatives_count': 0,
        'incident_count': 0,
        'closure_count': 0,
        'connector_summary': connector_summary,
    }


async def get_route_data(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    transport_type: str,
    locale: str = 'en',
    route_style: str = 'smart',
) -> dict[str, Any]:
    straight_distance_m = _haversine_distance_m(start_lat, start_lon, end_lat, end_lon)

    try:
        return await _get_osrm_route_data(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            transport_type=transport_type,
            locale=locale,
            route_style=route_style,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('OSRM route request failed: %s', exc)

    if settings.MAPBOX_ACCESS_TOKEN:
        try:
            return await _get_mapbox_route_data(
                start_lat=start_lat,
                start_lon=start_lon,
                end_lat=end_lat,
                end_lon=end_lon,
                transport_type=transport_type,
                locale=locale,
                route_style=route_style,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception('Mapbox route request failed: %s', exc)

    if settings.ORS_API_KEY:
        try:
            return await _get_ors_route_data(
                start_lat=start_lat,
                start_lon=start_lon,
                end_lat=end_lat,
                end_lon=end_lon,
                transport_type=transport_type,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception('ORS route request failed: %s', exc)

    profile = PROFILE_MAP.get(transport_type, PROFILE_MAP['car'])['ors']
    return {
        'geometry': _fallback_geometry(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            profile=profile,
            source='fallback',
            transport_type=transport_type,
        ),
        'distance_m': straight_distance_m,
        'duration_s': _estimated_duration_s(straight_distance_m, transport_type),
        'typical_duration_s': _estimated_duration_s(straight_distance_m, transport_type),
        'provider': 'fallback',
        'profile': profile,
        'steps': [],
        'alternatives_count': 0,
        'incident_count': 0,
        'closure_count': 0,
        'connector_summary': _empty_connector_summary(),
    }


async def get_traffic_insight(
    *,
    transport_type: str,
    route: dict[str, Any],
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    locale: str,  # noqa: ARG001
) -> dict[str, Any]:
    if transport_type != 'car':
        return {
            'level': 'low',
            'delay_minutes': 0,
            'source': 'mode',
            'message': 'Traffic pressure is insignificant for this transport mode.',
            'applied_to_eta': True,
        }

    if route.get('provider') == 'mapbox':
        duration_s = route.get('duration_s', 0)
        typical_duration_s = route.get('typical_duration_s', duration_s)
        delay_minutes = max(0, round((duration_s - typical_duration_s) / 60))
        congestion_values = [
            value
            for value in route.get('geometry', {}).get('properties', {}).get('segment_congestion_numeric', [])
            if isinstance(value, int | float)
        ]
        max_congestion = max(congestion_values, default=0)
        avg_congestion = sum(congestion_values) / len(congestion_values) if congestion_values else 0

        if delay_minutes >= 12 or max_congestion >= 70 or avg_congestion >= 50:
            level = 'high'
        elif delay_minutes >= 5 or max_congestion >= 35 or avg_congestion >= 25:
            level = 'medium'
        else:
            level = 'low'

        closure_count = route.get('closure_count', 0)
        incident_count = route.get('incident_count', 0)
        if closure_count:
            message = 'Live traffic detected closures along the corridor, so the route was recalculated around them.'
        elif incident_count:
            message = 'Live traffic incidents were detected on the corridor and folded into the ETA.'
        elif delay_minutes > 0:
            message = 'Live traffic slightly slows this route right now, and the ETA already includes that delay.'
        else:
            message = 'The corridor is flowing well right now according to live traffic.'

        return {
            'level': level,
            'delay_minutes': delay_minutes,
            'source': 'mapbox-live',
            'message': message,
            'incident_count': incident_count,
            'closure_count': closure_count,
            'applied_to_eta': True,
        }

    local_hour = datetime.now(ZoneInfo('Asia/Bishkek')).hour
    urban_bias = min(_distance_to_bishkek_km(start_lat, start_lon), _distance_to_bishkek_km(end_lat, end_lon)) < 60
    duration_s = route.get('duration_s', 0)
    if urban_bias and local_hour in {8, 9, 17, 18, 19}:
        factor = 0.22
        level = 'high'
    elif urban_bias and local_hour in {7, 10, 16, 20}:
        factor = 0.12
        level = 'medium'
    else:
        factor = 0.05
        level = 'low'

    delay_minutes = round((duration_s * factor) / 60)
    return {
        'level': level,
        'delay_minutes': delay_minutes,
        'source': 'heuristic',
        'message': (
            'Estimated from local time and route proximity to Bishkek traffic corridors.'
            if urban_bias
            else 'Mountain and regional roads are expected to stay relatively stable right now.'
        ),
        'applied_to_eta': False,
    }


def build_navigation_meta(
    *,
    duration_s: float,
    typical_duration_s: float | None,
    distance_m: float,
    traffic: dict[str, Any],
    transport_type: str,
    route_style: str,
    alternatives_count: int,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    eta_minutes = max(1, round(duration_s / 60))
    typical_eta_minutes = max(1, round((typical_duration_s or duration_s) / 60))
    return {
        'eta_minutes': eta_minutes,
        'typical_eta_minutes': typical_eta_minutes,
        'distance_km': round(distance_m / 1000, 1),
        'speed_profile': PROFILE_MAP.get(transport_type, PROFILE_MAP['car'])['osrm'],
        'fastest_route': False,
        'recommended_label': 'Smart mapped route',
        'alternative_routes': alternatives_count,
        'step_count': len(steps),
        'route_style': route_style,
        'traffic': traffic,
    }


def _connector_analysis_note(
    *,
    locale: str,
    transport_type: str,
    connector_summary: dict[str, Any] | None,
) -> str:
    summary = connector_summary or {}
    walk_distance_m = float(summary.get('walk_distance_m') or 0)
    if walk_distance_m <= 0:
        return ''

    walk_label = _format_distance_label(walk_distance_m, locale)
    if locale == 'ru':
        if transport_type == 'car':
            return f' Последний недоступный для авто участок отмечен пунктиром и построен по пешеходной сети: около {walk_label} придётся пройти пешком.'
        if transport_type == 'bike':
            return f' Участок, где велосипед уже не проходит, отмечен пунктиром и добирается по walking-сети: около {walk_label} нужно пройти пешком.'
        return f' Там, где пешеходная сеть заканчивается, остаётся около {walk_label}; этот кусок показан отдельно как осторожный пеший добор.'

    if locale == 'ky':
        if transport_type == 'car':
            return f' Унаа жүрбөгөн акыркы бөлүк пунктир менен белгиленип, жөө тармак менен эсептелди: болжол {walk_label} жөө өтөсүз.'
        if transport_type == 'bike':
            return f' Велосипед өтпөгөн бөлүк пунктир менен белгиленип, жөө тармак менен эсептелди: болжол {walk_label} жөө өтөсүз.'
        return f' Жөө тармак бүткөндөн кийинки акыркы {walk_label} өзүнчө этият бөлүк катары көрсөтүлдү.'

    if transport_type == 'car':
        return f' The final non-drivable section is shown as dashed and follows the walking network: about {walk_label} on foot.'
    if transport_type == 'bike':
        return f' The section where riding stops is shown as dashed and follows the walking network: about {walk_label} on foot.'
    return f' About {walk_label} remains beyond the mapped walking network and is shown as a separate cautious walking access.'


def _provider_analysis_note(locale: str, provider: str) -> str:
    if provider != 'fallback':
        return ''
    if locale == 'ru':
        return ' Сервис дорог сейчас недоступен, поэтому линия показана как оценочная аппроксимация.'
    if locale == 'ky':
        return ' Жол сервиси жеткиликсиз болгондуктан, линия болжолдуу түрдө көрсөтүлдү.'
    return ' Road-network routing is unavailable right now, so the line is only an approximation.'


def build_route_briefing(
    *,
    location_name: str,
    transport_type: str,
    route_style: str,
    locale: str,
    distance_m: float,
    duration_s: float,
    traffic: dict[str, Any],
    steps: list[dict[str, Any]],
    provider: str,
    connector_summary: dict[str, Any] | None = None,
) -> tuple[str, str]:
    copy = _copy(locale)
    traffic_level = traffic.get('level', 'low')
    style_label = copy['style'].get(route_style, copy['style']['smart'])
    transport_label = _route_mode_label(locale, transport_type)
    eta_minutes = max(1, round(duration_s / 60))
    delay_minutes = traffic.get('delay_minutes', 0)
    distance_km = round(distance_m / 1000, 1)

    if transport_type == 'car':
        analysis = copy['analysis'].format(
            style_label=style_label,
            location=location_name,
            distance_km=distance_km,
            eta_minutes=eta_minutes,
            traffic_label=copy['traffic'][traffic_level],
            delay_minutes=delay_minutes,
        )
    else:
        analysis = copy['analysis_mode'].format(
            style_label=style_label,
            location=location_name,
            distance_km=distance_km,
            eta_minutes=eta_minutes,
            transport_label=transport_label,
        )

    analysis += _connector_analysis_note(
        locale=locale,
        transport_type=transport_type,
        connector_summary=connector_summary,
    )
    analysis += _provider_analysis_note(locale, provider)

    first_step = next((step['voice_announcement'] or step['instruction'] for step in steps if step['instruction']), None)
    traffic_sentence = copy['traffic_sentence'][traffic_level]
    if first_step:
        voice_script = copy['voice'].format(
            location=location_name,
            transport_label=transport_label,
            traffic_sentence=traffic_sentence,
            first_step=first_step,
        )
    else:
        voice_script = copy['voice_no_steps'].format(
            location=location_name,
            transport_label=transport_label,
            traffic_sentence=traffic_sentence,
        )

    return analysis, voice_script


async def get_route_polyline(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    transport_type: str,
) -> dict[str, Any]:
    route = await get_route_data(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        transport_type=transport_type,
    )
    return route['geometry']

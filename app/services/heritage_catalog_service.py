import html
import logging
import re
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.data.cultural_layers import CURATED_CULTURAL_LAYERS, CURATED_LAYER_BY_ID
from app.data.heritage_snapshot import HERITAGE_SNAPSHOT, SNAPSHOT_BY_ID, SOURCE_MEDIA_URL, SOURCE_SITE_URL
from app.schemas.explorer_schemas import ExplorerLocationDetail, ExplorerLocationSummary

logger = logging.getLogger(__name__)

REMOTE_API_BASE = 'https://petroglyphs.murat.app/api'
CACHE_TTL = timedelta(minutes=30)
DETAIL_TTL = timedelta(hours=6)


def _strip_html(value: str | None) -> str:
    if not value:
        return ''
    text = re.sub(r'<[^>]+>', ' ', value)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _absolute_media(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith('http://') or path.startswith('https://'):
        return path
    return f'{SOURCE_MEDIA_URL}{path}'


def _expires_at(delta: timedelta) -> datetime:
    return datetime.now(UTC) + delta


def _is_fresh(expires_at: datetime | None) -> bool:
    return bool(expires_at and expires_at > datetime.now(UTC))


def _infer_terrain(region: str) -> str:
    normalized = region.lower()
    if 'иссык' in normalized:
        return 'lake'
    if 'чуй' in normalized:
        return 'valley'
    if 'ош' in normalized:
        return 'city'
    return 'mountain'


def _infer_seasonality(region: str, kind: str) -> str:
    if kind == 'calendar_event':
        return 'warm_season'
    normalized = region.lower()
    if 'нарын' in normalized or 'талас' in normalized:
        return 'summer_only'
    return 'all_season'


def _build_travel_tags(item: dict[str, Any], kind: str) -> list[str]:
    if item.get('travel_tags'):
        return list(item['travel_tags'])
    if kind == 'sacred_site':
        return ['ritual', 'quiet']
    if kind == 'calendar_event':
        return ['calendar', 'seasonal']
    return ['petroglyph', 'heritage']


class HeritageCatalogService:
    def __init__(self) -> None:
        self._list_cache: dict[str, Any] = {'expires_at': None, 'items': None, 'source_provider': 'snapshot'}
        self._detail_cache: dict[int, dict[str, Any]] = {}

    def _snapshot_items(self) -> list[dict[str, Any]]:
        return deepcopy(HERITAGE_SNAPSHOT + CURATED_CULTURAL_LAYERS)

    def _build_source_url(self, source_id: int) -> str:
        return f'{SOURCE_SITE_URL}/{source_id}'

    def _generic_summary(self, name: str) -> str:
        return f'{name} из каталога комплексов петроглифов Центральной Азии.'

    def _summary_from_detail(self, detail_text: str, fallback: str) -> str:
        if not detail_text:
            return fallback
        first_sentence = re.split(r'(?<=[.!?])\s+', detail_text, maxsplit=1)[0].strip()
        return first_sentence[:220] if first_sentence else fallback

    async def _fetch_remote_json(self, path: str) -> dict[str, Any]:
        url = f'{REMOTE_API_BASE}{path}'
        async with httpx.AsyncClient(timeout=20, headers={'User-Agent': 'NomadHeritage/1.0'}) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def _normalize_snapshot_location(self, item: dict[str, Any]) -> ExplorerLocationSummary:
        kind = item.get('kind', 'petroglyph')
        return ExplorerLocationSummary(
            source_id=item['source_id'],
            name=item['name'],
            region=item['region'],
            summary=item['summary'],
            image_url=item.get('image_url'),
            latitude=item.get('latitude'),
            longitude=item.get('longitude'),
            coordinate_quality=item.get('coordinate_quality', 'missing'),
            kind=kind,
            terrain=item.get('terrain', _infer_terrain(item['region'])),
            seasonality=item.get('seasonality', _infer_seasonality(item['region'], kind)),
            travel_tags=_build_travel_tags(item, kind),
            featured=item.get('featured', False),
            route_available=item.get('latitude') is not None and item.get('longitude') is not None,
            source_url=item.get('source_url') or self._build_source_url(item['source_id']),
        )

    def _merge_remote_with_snapshot(
        self,
        remote_items: list[dict[str, Any]],
    ) -> list[ExplorerLocationSummary]:
        merged: list[ExplorerLocationSummary] = []
        seen_ids: set[int] = set()

        for remote in remote_items:
            source_id = int(remote['id'])
            snapshot = SNAPSHOT_BY_ID.get(source_id, {})
            latitude = snapshot.get('latitude')
            longitude = snapshot.get('longitude')
            kind = snapshot.get('kind', 'petroglyph')
            merged.append(
                ExplorerLocationSummary(
                    source_id=source_id,
                    name=remote['name'],
                    region=snapshot.get('region', remote.get('countryName', 'Кыргызстан')),
                    summary=snapshot.get('summary', self._generic_summary(remote['name'])),
                    image_url=_absolute_media(remote.get('mainImage')) or snapshot.get('image_url'),
                    latitude=latitude,
                    longitude=longitude,
                    coordinate_quality=snapshot.get('coordinate_quality', 'missing'),
                    kind=kind,
                    terrain=snapshot.get('terrain', _infer_terrain(snapshot.get('region', remote.get('countryName', 'Кыргызстан')))),
                    seasonality=snapshot.get(
                        'seasonality',
                        _infer_seasonality(snapshot.get('region', remote.get('countryName', 'Кыргызстан')), kind),
                    ),
                    travel_tags=_build_travel_tags(snapshot, kind),
                    featured=snapshot.get('featured', False),
                    route_available=latitude is not None and longitude is not None,
                    source_url=self._build_source_url(source_id),
                )
            )
            seen_ids.add(source_id)

        for snapshot in self._snapshot_items():
            if snapshot['source_id'] in seen_ids:
                continue
            merged.append(self._normalize_snapshot_location(snapshot))

        return sorted(
            merged,
            key=lambda item: (
                not item.featured,
                not item.route_available,
                item.coordinate_quality != 'verified',
                item.name.lower(),
            ),
        )

    async def list_locations(self) -> tuple[list[ExplorerLocationSummary], str]:
        if _is_fresh(self._list_cache['expires_at']) and self._list_cache['items'] is not None:
            return self._list_cache['items'], self._list_cache['source_provider']

        snapshot_items = [self._normalize_snapshot_location(item) for item in self._snapshot_items()]
        try:
            payload = await self._fetch_remote_json('/petroglyphs/?country=kyrgyzstan&page_size=100')
            remote_items = payload.get('items', [])
            items = self._merge_remote_with_snapshot(remote_items)
            source_provider = 'remote+snapshot'
        except Exception as exc:  # noqa: BLE001
            logger.warning('Heritage remote list fetch failed, using snapshot only: %s', exc)
            items = sorted(snapshot_items, key=lambda item: (not item.featured, item.name.lower()))
            source_provider = 'snapshot'

        self._list_cache = {
            'expires_at': _expires_at(CACHE_TTL),
            'items': items,
            'source_provider': source_provider,
        }
        return items, source_provider

    async def _fetch_remote_map_center(self, source_id: int) -> tuple[float, float] | None:
        try:
            payload = await self._fetch_remote_json(f'/petroglyphs/{source_id}/map')
        except Exception:  # noqa: BLE001
            return None

        center = payload.get('center') or {}
        lat = center.get('lat')
        lng = center.get('lng')
        if lat is None or lng is None:
            return None
        return float(lat), float(lng)

    async def get_location_detail(self, source_id: int) -> ExplorerLocationDetail | None:
        cached = self._detail_cache.get(source_id)
        if cached and _is_fresh(cached.get('expires_at')):
            return cached['item']

        items, _ = await self.list_locations()
        base = next((item for item in items if item.source_id == source_id), None)
        snapshot = SNAPSHOT_BY_ID.get(source_id, {}) | CURATED_LAYER_BY_ID.get(source_id, {})
        if base is None and not snapshot:
            return None

        if base is None:
            base = self._normalize_snapshot_location(snapshot)

        detail = ExplorerLocationDetail(
            **base.model_dump(),
            gallery=[base.image_url] if base.image_url else [],
            archaeological_description=base.summary,
            ethnographic_description=None,
            source_provider='snapshot',
        )

        if base.kind != 'petroglyph':
            self._detail_cache[source_id] = {'expires_at': _expires_at(DETAIL_TTL), 'item': detail}
            return detail

        try:
            payload = await self._fetch_remote_json(f'/petroglyphs/{source_id}/')
            archaeology = _strip_html(payload.get('archaeologicalDescription'))
            ethnography = _strip_html(payload.get('ethnographicDescription'))
            gallery = [_absolute_media(item.get('image')) for item in payload.get('images', [])]
            gallery = [item for item in gallery if item]
            coords = (detail.latitude, detail.longitude)
            if detail.latitude is None or detail.longitude is None:
                center = await self._fetch_remote_map_center(source_id)
                if center:
                    coords = center

            detail = ExplorerLocationDetail(
                source_id=source_id,
                name=payload.get('name') or detail.name,
                region=snapshot.get('region', payload.get('countryName', detail.region)),
                summary=self._summary_from_detail(archaeology, detail.summary),
                image_url=(gallery[0] if gallery else detail.image_url),
                latitude=coords[0] if coords[0] is not None else None,
                longitude=coords[1] if coords[1] is not None else None,
                coordinate_quality=(
                    detail.coordinate_quality
                    if detail.coordinate_quality != 'missing' or coords[0] is None
                    else 'verified'
                ),
                kind=detail.kind,
                terrain=detail.terrain,
                seasonality=detail.seasonality,
                travel_tags=detail.travel_tags,
                featured=detail.featured,
                route_available=coords[0] is not None and coords[1] is not None,
                source_url=self._build_source_url(source_id),
                gallery=gallery or detail.gallery,
                archaeological_description=archaeology or detail.archaeological_description,
                ethnographic_description=ethnography or detail.ethnographic_description,
                source_provider='remote+snapshot',
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning('Heritage remote detail fetch failed for %s: %s', source_id, exc)

        self._detail_cache[source_id] = {'expires_at': _expires_at(DETAIL_TTL), 'item': detail}
        return detail


heritage_catalog_service = HeritageCatalogService()

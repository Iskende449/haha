import {
  Bike,
  Car,
  List,
  MapPinned,
  MoonStar,
  Navigation,
  Route,
  Sparkles,
  SunMedium,
  Flame,
} from 'lucide-react'

export const DEFAULT_USER_POSITION = [42.8746, 74.6122]
export const LOCALE = 'ru'

export const KIND_META = {
  all: { label: 'Все точки', icon: Sparkles, accent: '#f7efe3' },
  petroglyph: { label: 'Петроглифы', icon: SunMedium, accent: '#f4c95d' },
  sacred_site: { label: 'Сакральные места', icon: Flame, accent: '#ff7b37' },
  calendar_event: { label: 'Традиционный календарь', icon: MoonStar, accent: '#ffe36c' },
}

export const TERRAIN_FILTERS = {
  all: 'Любой рельеф',
  mountain: 'Горы',
  lake: 'Озеро',
  valley: 'Долина',
  steppe: 'Степь',
  city: 'Город',
}

export const TRANSPORTS = {
  car: { label: 'Авто', icon: Car },
  bike: { label: 'Вело', icon: Bike },
  foot: { label: 'Пешком', icon: Navigation },
}

export const TRANSPORT_ACCENTS = {
  car: '#ff7b37',
  bike: '#6de2a6',
  foot: '#ffd98a',
}

export const SMART_ROUTE_META = {
  title: 'Продуманный маршрут',
  description:
    'Для машины строится путь по дорогам с пешим добором в конце. Для велосипеда используется вело-проходимая сеть и пеший добор только если он нужен. Для пешего режима строится отдельный маршрут по walking-сети.',
}

export const PANEL_TABS = {
  place: { label: 'Точка', icon: MapPinned },
  route: { label: 'Маршрут', icon: Route },
  list: { label: 'Список', icon: List },
}

export function distanceBetween([lat1, lon1], [lat2, lon2]) {
  const radius = 6371e3
  const phi1 = (lat1 * Math.PI) / 180
  const phi2 = (lat2 * Math.PI) / 180
  const dPhi = ((lat2 - lat1) * Math.PI) / 180
  const dLambda = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dPhi / 2) * Math.sin(dPhi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) * Math.sin(dLambda / 2)
  return radius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function pathDistance(coordinates = []) {
  if (coordinates.length < 2) return 0

  return coordinates.slice(0, -1).reduce((total, [lon, lat], index) => {
    const [nextLon, nextLat] = coordinates[index + 1]
    return total + distanceBetween([lat, lon], [nextLat, nextLon])
  }, 0)
}

export function formatDistance(meters) {
  if (!Number.isFinite(meters) || meters <= 0) return '...'
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)} км`
  return `${Math.round(meters)} м`
}

export function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return '...'
  const totalMinutes = Math.max(1, Math.round(seconds / 60))
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours === 0) return `${minutes} мин`
  return `${hours} ч ${minutes} мин`
}

export function trafficLabel(level) {
  if (level === 'high') return 'Плотно'
  if (level === 'medium') return 'Средне'
  return 'Свободно'
}

export function qualityLabel(quality) {
  if (quality === 'verified') return 'Точная точка'
  if (quality === 'approximate') return 'Примерная точка'
  return 'Без координат'
}

export function providerLabel(provider) {
  if (provider === 'mapbox') return 'Mapbox live'
  if (provider === 'osrm') return 'OSRM smart route'
  if (provider === 'openrouteservice') return 'OpenRouteService'
  return 'Оценочная линия'
}

export function seasonalityLabel(seasonality) {
  if (seasonality === 'summer_only') return 'Лучше летом'
  if (seasonality === 'warm_season') return 'Тёплый сезон'
  return 'Круглый год'
}

export function getRenderSegments(routeGeometry, transportMode = 'car', serverSegments = null) {
  if (Array.isArray(serverSegments) && serverSegments.length > 0) {
    return serverSegments.map((segment, index) => ({
      id: segment.id || `${segment.kind || 'segment'}-${segment.mode || transportMode}-${index}`,
      ...segment,
      distance_m: Number(segment.distance_m) || pathDistance(segment.coordinates),
      duration_s: Number(segment.duration_s) || 0,
      transport_context: segment.transport_context || segment.mode || transportMode,
    }))
  }

  const explicitSegments = routeGeometry?.properties?.render_segments
  if (Array.isArray(explicitSegments) && explicitSegments.length > 0) {
    return explicitSegments.map((segment, index) => ({
      id: `${segment.kind || 'segment'}-${segment.mode || transportMode}-${index}`,
      ...segment,
      distance_m: Number(segment.distance_m) || pathDistance(segment.coordinates),
      duration_s: Number(segment.duration_s) || 0,
      transport_context: segment.transport_context || segment.mode || transportMode,
    }))
  }

  const coordinates = routeGeometry?.geometry?.coordinates || []
  if (coordinates.length < 2) return []

  return [
    {
      id: 'route-fallback',
      kind: routeGeometry?.properties?.source === 'fallback' ? 'approximation' : 'network',
      mode: transportMode,
      dashed: routeGeometry?.properties?.source === 'fallback',
      distance_m: pathDistance(coordinates),
      duration_s: 0,
      label: routeGeometry?.properties?.source === 'fallback' ? 'Оценочная линия' : 'Маршрут по сети',
      coordinates,
      transport_context: transportMode,
    },
  ]
}

export function buildRouteBreakdown(routeGeometry, transportMode = 'car', serverSegments = null) {
  const segments = getRenderSegments(routeGeometry, transportMode, serverSegments)
  const networkDistanceByMode = { car: 0, bike: 0, foot: 0 }
  let connectorDistanceM = 0
  let approximationDistanceM = 0

  segments.forEach((segment) => {
    const distance = Number(segment.distance_m) || 0
    const context = segment.transport_context || segment.mode || transportMode

    if (segment.kind === 'walk_connector') {
      connectorDistanceM += distance
      return
    }

    if (segment.kind === 'approximation') {
      approximationDistanceM += distance
      return
    }

    networkDistanceByMode[context] = (networkDistanceByMode[context] || 0) + distance
  })

  return {
    segments,
    networkDistanceByMode,
    connectorDistanceM,
    approximationDistanceM,
    hasConnector: connectorDistanceM > 0,
    hasApproximation: approximationDistanceM > 0,
  }
}

export function segmentTitle(segment) {
  const context = segment.transport_context || segment.mode

  if (segment.kind === 'approximation') return 'Оценочная линия'
  if (segment.kind === 'walk_connector') {
    if (context === 'car') return 'После авто пешком'
    if (context === 'bike') return 'После вело пешком'
    return 'Пеший добор'
  }

  if (context === 'car') return 'Участок для машины'
  if (context === 'bike') return 'Участок для велосипеда'
  return 'Пеший маршрут'
}

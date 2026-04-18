import { Fragment, useEffect, useMemo } from 'react'
import { Circle, MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from 'react-leaflet'
import L from 'leaflet'

import { getRenderSegments } from '@/components/home/home-utils'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN

const TILESETS = {
  night: MAPBOX_TOKEN
    ? {
        url: `https://api.mapbox.com/styles/v1/mapbox/navigation-night-v1/tiles/512/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`,
        attribution:
          '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noreferrer">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>',
        tileSize: 512,
        zoomOffset: -1,
        maxZoom: 20,
      }
    : {
        url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">CARTO</a>',
        maxZoom: 19,
      },
  dawn: MAPBOX_TOKEN
    ? {
        url: `https://api.mapbox.com/styles/v1/mapbox/navigation-day-v1/tiles/512/{z}/{x}/{y}@2x?access_token=${MAPBOX_TOKEN}`,
        attribution:
          '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noreferrer">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>',
        tileSize: 512,
        zoomOffset: -1,
        maxZoom: 20,
      }
    : {
        url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">CARTO</a>',
        maxZoom: 19,
      },
}

const KIND_META = {
  petroglyph: {
    accent: '#f4c95d',
    icon: `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="4.5" stroke="currentColor" stroke-width="1.6"/>
        <path d="M12 2.8v3.1M12 18.1v3.1M2.8 12h3.1M18.1 12h3.1M5.2 5.2l2.2 2.2M16.6 16.6l2.2 2.2M18.8 5.2l-2.2 2.2M7.4 16.6l-2.2 2.2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    `,
  },
  sacred_site: {
    accent: '#ff7b37',
    icon: `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 3.5c2.8 3.1 5.4 6 5.4 9.1a5.4 5.4 0 1 1-10.8 0c0-3.1 2.6-6 5.4-9.1Z" fill="currentColor"/>
        <path d="M12 8.4c1.3 1.5 2.2 2.7 2.2 4a2.2 2.2 0 0 1-4.4 0c0-1.3.9-2.5 2.2-4Z" fill="#1a100c"/>
      </svg>
    `,
  },
  calendar_event: {
    accent: '#ffe36c',
    icon: `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M15.6 4.8a6.8 6.8 0 1 0 3.6 12.5A7.4 7.4 0 1 1 15.6 4.8Z" fill="currentColor"/>
        <circle cx="17.6" cy="7.4" r="1.4" fill="currentColor"/>
      </svg>
    `,
  },
}

const MODE_STYLES = {
  car: {
    solid: '#ff7b37',
    connector: '#ffd6b8',
    shadow: 'rgba(18, 10, 8, 0.86)',
  },
  bike: {
    solid: '#69dfa4',
    connector: '#c9f9df',
    shadow: 'rgba(7, 22, 15, 0.82)',
  },
  foot: {
    solid: '#ffe08a',
    connector: '#fff0c2',
    shadow: 'rgba(37, 29, 12, 0.84)',
  },
}

function createLocationIcon({ kind, active }) {
  const meta = KIND_META[kind] || KIND_META.petroglyph
  const size = active ? 42 : 34
  const glow = active ? `0 0 0 1px rgba(255,255,255,0.18), 0 10px 30px ${meta.accent}88` : `0 8px 18px ${meta.accent}4A`

  return new L.DivIcon({
    html: `
      <div style="
        width:${size}px;
        height:${size}px;
        display:flex;
        align-items:center;
        justify-content:center;
        border-radius:999px;
        border:1px solid rgba(255,255,255,0.14);
        background:radial-gradient(circle at 30% 30%, rgba(255,255,255,0.16), rgba(10,7,6,0.96));
        color:${meta.accent};
        box-shadow:${glow};
        backdrop-filter:blur(6px);
      ">
        ${meta.icon}
      </div>
    `,
    className: '',
    iconAnchor: [size / 2, size / 2],
  })
}

const userIcon = new L.DivIcon({
  html: `
    <div style="
      width: 20px;
      height: 20px;
      border-radius: 999px;
      background: #f6efe6;
      border: 4px solid #ff7b37;
      box-shadow: 0 0 0 10px rgba(255,123,55,0.18), 0 18px 36px rgba(0,0,0,0.36);
    "></div>
  `,
  className: '',
  iconAnchor: [10, 10],
})

function segmentStyle(segment) {
  const context = segment.transport_context || segment.mode || 'car'
  const palette = MODE_STYLES[context] || MODE_STYLES.car

  if (segment.kind === 'approximation') {
    return {
      color: '#f7efe3',
      shadowColor: 'rgba(12, 10, 10, 0.78)',
      dashArray: '12 14',
      weight: 5,
      opacity: 0.82,
    }
  }

  if (segment.kind === 'walk_connector') {
    if (context === 'foot') {
      return {
        color: palette.solid,
        shadowColor: palette.shadow,
        dashArray: undefined,
        weight: 6,
        opacity: 0.98,
      }
    }

    return {
      color: palette.connector,
      shadowColor: palette.shadow,
      dashArray: context === 'car' ? '12 10' : context === 'bike' ? '7 9' : '4 8',
      weight: 5,
      opacity: 0.96,
    }
  }

  return {
    color: palette.solid,
    shadowColor: palette.shadow,
    dashArray: undefined,
    weight: 7,
    opacity: 0.98,
  }
}

function MapViewportController({ routePositions, selectedPosition, userPosition }) {
  const map = useMap()

  useEffect(() => {
    const isDesktop = typeof window !== 'undefined' && window.innerWidth >= 1024

    if (routePositions.length > 1) {
      map.fitBounds(routePositions, {
        paddingTopLeft: isDesktop ? [380, 40] : [24, 132],
        paddingBottomRight: isDesktop ? [40, 40] : [24, 220],
        maxZoom: 13,
      })
      return
    }

    if (selectedPosition) {
      map.setView(selectedPosition, isDesktop ? 11 : 10, { animate: true })
      return
    }

    map.setView(userPosition, 8, { animate: true })
  }, [map, routePositions, selectedPosition, userPosition])

  return null
}

export function MapView({
  userPosition,
  locations,
  selectedLocation,
  routeGeometry,
  routeTransport = 'car',
  onSelectLocation,
  theme = 'night',
}) {
  const tileConfig = TILESETS[theme] || TILESETS.night

  const routeSegments = useMemo(() => {
    return getRenderSegments(routeGeometry, routeTransport)
      .filter((segment) => Array.isArray(segment.coordinates) && segment.coordinates.length > 1)
      .map((segment, index) => ({
        ...segment,
        id: segment.id || `${segment.kind || 'segment'}-${index}`,
        positions: segment.coordinates.map(([lon, lat]) => [lat, lon]),
        style: segmentStyle(segment),
      }))
  }, [routeGeometry, routeTransport])

  const routePositions = useMemo(() => {
    const coordinates = routeGeometry?.geometry?.coordinates || []
    if (coordinates.length > 1) {
      return coordinates.map(([lon, lat]) => [lat, lon])
    }
    return routeSegments.flatMap((segment) => segment.positions)
  }, [routeGeometry, routeSegments])

  const selectedPosition = Number.isFinite(selectedLocation?.latitude) && Number.isFinite(selectedLocation?.longitude)
    ? [selectedLocation.latitude, selectedLocation.longitude]
    : null

  return (
    <MapContainer
      center={userPosition}
      zoom={8}
      scrollWheelZoom
      zoomControl={false}
      className='navigator-map h-screen w-full'
      preferCanvas
    >
      <TileLayer {...tileConfig} />

      <MapViewportController
        routePositions={routePositions}
        selectedPosition={selectedPosition}
        userPosition={userPosition}
      />

      <Circle
        center={userPosition}
        radius={130}
        pathOptions={{ color: '#ff9f43', fillColor: '#ff7b37', fillOpacity: 0.08, weight: 1 }}
      />

      <Marker position={userPosition} icon={userIcon}>
        <Tooltip direction='top' offset={[0, -10]}>Вы здесь</Tooltip>
      </Marker>

      {locations
        .filter((location) => Number.isFinite(location.latitude) && Number.isFinite(location.longitude))
        .map((location) => {
          const isActive = location.source_id === selectedLocation?.source_id

          return (
            <Marker
              key={location.source_id}
              position={[location.latitude, location.longitude]}
              icon={createLocationIcon({ kind: location.kind, active: isActive })}
              eventHandlers={{ click: () => onSelectLocation(location) }}
            >
              <Tooltip direction='top' offset={[0, -12]}>
                {location.name}
              </Tooltip>
            </Marker>
          )
        })}

      {routeSegments.length > 0
        ? routeSegments.map((segment) => (
          <Fragment key={segment.id}>
            <Polyline
              positions={segment.positions}
              pathOptions={{
                color: segment.style.shadowColor,
                weight: segment.style.weight + 5,
                opacity: 0.74,
                lineCap: 'round',
                lineJoin: 'round',
                dashArray: segment.style.dashArray,
              }}
            />
            <Polyline
              positions={segment.positions}
              pathOptions={{
                color: segment.style.color,
                weight: segment.style.weight,
                opacity: segment.style.opacity,
                lineCap: 'round',
                lineJoin: 'round',
                dashArray: segment.style.dashArray,
              }}
            />
          </Fragment>
        ))
        : null}
    </MapContainer>
  )
}

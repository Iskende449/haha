import { motion as Motion } from 'framer-motion'
import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'

import { HomeHeaderPanel } from '@/components/home/HomeHeaderPanel'
import { LocationPanel } from '@/components/home/LocationPanel'
import { LocationsPanel } from '@/components/home/LocationsPanel'
import { PanelTabButton } from '@/components/home/HomePrimitives'
import { RoutePanel } from '@/components/home/RoutePanel'
import {
  DEFAULT_USER_POSITION,
  LOCALE,
  PANEL_TABS,
} from '@/components/home/home-utils'
import { MapView } from '@/components/map/MapView'
import { VibeLoader } from '@/components/ui/VibeLoader'
import { useAuth } from '@/hooks/useAuth'
import { useExplorerBootstrap, useExplorerLocation, useExplorerLocations, useExplorerRoute } from '@/hooks/useExplorer'
import { useNavigatorSettings } from '@/hooks/useNavigatorSettings'
import { useRouteVoice } from '@/hooks/useRouteVoice'
import { toApiErrorMessage } from '@/services/api'

const EMPTY_LOCATIONS = []

export default function Home() {
  const { user, logout } = useAuth()
  const { settings, updateSettings } = useNavigatorSettings()
  const [transport, setTransport] = useState('car')
  const [kindFilter, setKindFilter] = useState('all')
  const [terrainFilter, setTerrainFilter] = useState('all')
  const [verifiedOnly, setVerifiedOnly] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [routeData, setRouteData] = useState(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [userPosition, setUserPosition] = useState(DEFAULT_USER_POSITION)
  const [panelTab, setPanelTab] = useState('place')

  const deferredQuery = useDeferredValue(query)
  const bootstrapQuery = useExplorerBootstrap()
  const locationsQuery = useExplorerLocations({
    query: deferredQuery.trim() || undefined,
    kind: kindFilter,
    terrain: terrainFilter,
    verified_only: verifiedOnly,
    sort: 'smart',
    limit: 48,
    user_lat: userPosition[0],
    user_lon: userPosition[1],
  })
  const routeMutation = useExplorerRoute()
  const { speak, stop, selectedVoiceName, isSupported } = useRouteVoice({
    enabled: settings.voiceEnabled,
    locale: LOCALE,
  })
  const lastSpokenRouteRef = useRef(null)

  const allLocations = locationsQuery.data?.items ?? EMPTY_LOCATIONS

  useEffect(() => {
    if (!navigator.geolocation) return

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserPosition([position.coords.latitude, position.coords.longitude])
      },
      () => {},
      { enableHighAccuracy: true, maximumAge: 60_000, timeout: 7_000 },
    )
  }, [])

  const effectiveSelectedId =
    selectedId
    ?? locationsQuery.data?.recommended_source_id
    ?? allLocations[0]?.source_id
    ?? null

  const selectedSummary = useMemo(
    () => allLocations.find((item) => item.source_id === effectiveSelectedId) || null,
    [effectiveSelectedId, allLocations],
  )

  const detailQuery = useExplorerLocation(effectiveSelectedId, {
    user_lat: userPosition[0],
    user_lon: userPosition[1],
  })
  const activeLocation = detailQuery.data ? { ...(selectedSummary || {}), ...detailQuery.data } : selectedSummary
  const activeRouteData = routeData?.location?.source_id === effectiveSelectedId ? routeData : null
  const routeLocation = activeRouteData?.location ? { ...(selectedSummary || {}), ...activeRouteData.location } : activeLocation

  useEffect(() => {
    if (!settings.voiceEnabled) stop()
  }, [settings.voiceEnabled, stop])

  useEffect(() => {
    const voicePayload = activeRouteData?.voice_guidance
    const voiceText = voicePayload?.text || activeRouteData?.voice_script
    if (!voiceText || !settings.voiceEnabled) return

    const currentRouteKey = [
      activeRouteData.location?.source_id,
      activeRouteData.transport_mode,
      Math.round(activeRouteData.duration_s || 0),
    ].join(':')

    if (lastSpokenRouteRef.current === currentRouteKey) return
    lastSpokenRouteRef.current = currentRouteKey
    speak(voiceText, voicePayload)
  }, [activeRouteData, settings.voiceEnabled, speak])

  const handleSelectLocation = (location) => {
    startTransition(() => {
      setSelectedId(location.source_id)
      setRouteData((current) => (current?.location?.source_id === location.source_id ? current : null))
      setPanelTab('place')
    })
  }

  const handleTransportChange = (nextTransport) => {
    startTransition(() => {
      setTransport(nextTransport)
      setRouteData(null)
      setPanelTab('route')
    })
  }

  const handleBuildRoute = async () => {
    if (!activeLocation?.source_id || !activeLocation?.route_available) return

    try {
      const data = await routeMutation.mutateAsync({
        source_id: activeLocation.source_id,
        user_lat: userPosition[0],
        user_lon: userPosition[1],
        transport_mode: transport,
        locale: LOCALE,
      })
      setRouteData(data)
      setPanelTab('route')
    } catch {
      setPanelTab('route')
    }
  }

  const routeError = routeMutation.error ? toApiErrorMessage(routeMutation.error) : null
  const visibleLocations = allLocations.slice(0, 18)

  if (locationsQuery.isLoading && allLocations.length === 0) {
    return (
      <div className='flex min-h-screen items-center justify-center bg-[#120d0b]'>
        <VibeLoader label='Поднимаю карту, маршруты и сакральные точки...' />
      </div>
    )
  }

  return (
    <div className={`theme-${settings.theme} relative min-h-screen overflow-hidden bg-[var(--app-bg)] text-[var(--text-primary)]`}>
      <MapView
        userPosition={userPosition}
        locations={allLocations}
        selectedLocation={routeLocation || activeLocation}
        routeGeometry={activeRouteData?.route_geometry}
        routeSegments={activeRouteData?.render_segments}
        routeTransport={activeRouteData?.transport_mode || transport}
        onSelectLocation={handleSelectLocation}
        theme={settings.theme}
        viewport={activeRouteData?.viewport}
        mapConfig={bootstrapQuery.data?.map}
      />

      <div className='pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,216,170,0.16),transparent_34%),linear-gradient(180deg,rgba(9,7,7,0.22)_0%,rgba(9,7,7,0)_36%,rgba(9,7,7,0.78)_100%)]' />

      <div className='pointer-events-none absolute inset-x-0 top-0 z-[1000] px-4 pt-4 lg:left-4 lg:right-auto lg:w-[28rem] lg:px-0'>
        <Motion.div initial={{ opacity: 0, y: -18 }} animate={{ opacity: 1, y: 0 }} className='pointer-events-auto'>
          <HomeHeaderPanel
            user={user}
            logout={logout}
            query={query}
            onQueryChange={setQuery}
            settingsOpen={settingsOpen}
            setSettingsOpen={setSettingsOpen}
            filtersOpen={filtersOpen}
            setFiltersOpen={setFiltersOpen}
            settings={settings}
            updateSettings={updateSettings}
            selectedVoiceName={selectedVoiceName}
            kindFilter={kindFilter}
            setKindFilter={setKindFilter}
            terrainFilter={terrainFilter}
            setTerrainFilter={setTerrainFilter}
            verifiedOnly={verifiedOnly}
            setVerifiedOnly={setVerifiedOnly}
          />
        </Motion.div>
      </div>

      <div className='pointer-events-none absolute inset-x-0 bottom-0 z-[1000] px-4 pb-[calc(env(safe-area-inset-bottom)+16px)] lg:left-4 lg:right-auto lg:w-[28rem] lg:px-0 lg:pb-4'>
        <Motion.div
          initial={{ opacity: 0, y: 26 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08 }}
          className='pointer-events-auto rounded-[34px] border border-white/10 bg-[rgba(18,13,11,0.86)] p-4 shadow-[0_-18px_80px_rgba(0,0,0,0.48)] backdrop-blur-2xl'
        >
          <div className='mb-4 flex gap-2'>
            {Object.keys(PANEL_TABS).map((tabId) => (
              <PanelTabButton key={tabId} tabId={tabId} active={panelTab === tabId} onClick={setPanelTab} />
            ))}
          </div>

          <div className='max-h-[52vh] overflow-y-auto pr-1 lg:max-h-[calc(100vh-17rem)]'>
            {panelTab === 'place' ? <LocationPanel activeLocation={activeLocation} /> : null}

            {panelTab === 'route' ? (
              <RoutePanel
                routeData={activeRouteData}
                routeError={routeError}
                transport={transport}
                setTransport={handleTransportChange}
                activeLocation={activeLocation}
                onBuildRoute={handleBuildRoute}
                isLoading={routeMutation.isPending}
                settings={settings}
                speak={speak}
                isSupported={isSupported}
              />
            ) : null}

            {panelTab === 'list' ? (
              <LocationsPanel
                locations={visibleLocations}
                selectedId={effectiveSelectedId}
                onSelectLocation={handleSelectLocation}
              />
            ) : null}
          </div>
        </Motion.div>
      </div>
    </div>
  )
}

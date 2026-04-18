import { useEffect, useState } from 'react'

const SETTINGS_KEY = 'nomad_navigator_settings_v2'

const DEFAULT_SETTINGS = {
  theme: 'night',
  voiceEnabled: true,
}

function readStoredSettings() {
  if (typeof window === 'undefined') return DEFAULT_SETTINGS

  try {
    const raw = window.localStorage.getItem(SETTINGS_KEY)
    if (!raw) return DEFAULT_SETTINGS
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  }
  catch {
    return DEFAULT_SETTINGS
  }
}

export function useNavigatorSettings() {
  const [settings, setSettings] = useState(readStoredSettings)

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  }, [settings])

  const updateSettings = (patch) => {
    setSettings((current) => ({ ...current, ...patch }))
  }

  return {
    settings,
    updateSettings,
  }
}

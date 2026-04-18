import { useCallback, useEffect, useMemo, useState } from 'react'

const MALE_HINTS = [
  'male',
  'man',
  'alex',
  'david',
  'james',
  'pavel',
  'sergey',
  'igor',
  'yuri',
  'maksim',
  'thomas',
  'daniel',
]

function localeCandidates(locale) {
  if (locale === 'ru') return ['ru', 'ru-RU', 'ru_KG']
  if (locale === 'ky') return ['ky', 'ky-KG', 'ru', 'ru-RU']
  return ['en', 'en-US', 'en-GB']
}

function pickVoice(voices, locale) {
  if (!voices.length) return null

  const candidates = localeCandidates(locale)
  const localeMatches = voices.filter((voice) => candidates.some((candidate) => voice.lang?.startsWith(candidate)))
  const source = localeMatches.length ? localeMatches : voices

  const hinted = source.find((voice) => {
    const normalized = `${voice.name} ${voice.voiceURI}`.toLowerCase()
    return MALE_HINTS.some((hint) => normalized.includes(hint))
  })

  return hinted || source[0] || voices[0] || null
}

export function useRouteVoice({ enabled, locale }) {
  const [voices, setVoices] = useState([])

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return undefined

    const loadVoices = () => setVoices(window.speechSynthesis.getVoices())
    loadVoices()
    window.speechSynthesis.addEventListener('voiceschanged', loadVoices)

    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', loadVoices)
    }
  }, [])

  const voice = useMemo(() => pickVoice(voices, locale), [locale, voices])

  const stop = useCallback(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
  }, [])

  const speak = useCallback((text, options = {}) => {
    if (!enabled || !text || typeof window === 'undefined' || !('speechSynthesis' in window)) return

    window.speechSynthesis.cancel()

    const utterance = new window.SpeechSynthesisUtterance(text)
    const preferredLocale = options.locale || locale
    utterance.lang = voice?.lang || (preferredLocale === 'ru' ? 'ru-RU' : preferredLocale === 'ky' ? 'ky-KG' : 'en-US')
    utterance.voice = voice
    utterance.pitch = options.pitch ?? 0.82
    utterance.rate = options.rate ?? 0.94
    utterance.volume = options.volume ?? 1

    window.speechSynthesis.speak(utterance)
  }, [enabled, locale, voice])

  useEffect(() => {
    if (!enabled) stop()
  }, [enabled, stop])

  return {
    isSupported: typeof window !== 'undefined' && 'speechSynthesis' in window,
    selectedVoiceName: voice?.name || null,
    speak,
    stop,
  }
}

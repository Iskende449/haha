import { AnimatePresence, motion as Motion } from 'framer-motion'
import { LogOut, Search, Settings2, Volume2, VolumeX, X } from 'lucide-react'

import { FilterChip } from '@/components/home/HomePrimitives'
import { KIND_META, TERRAIN_FILTERS } from '@/components/home/home-utils'

export function HomeHeaderPanel({
  user,
  logout,
  query,
  onQueryChange,
  settingsOpen,
  setSettingsOpen,
  filtersOpen,
  setFiltersOpen,
  settings,
  updateSettings,
  selectedVoiceName,
  kindFilter,
  setKindFilter,
  terrainFilter,
  setTerrainFilter,
  verifiedOnly,
  setVerifiedOnly,
}) {
  return (
    <div className='rounded-[30px] border border-white/10 bg-[rgba(18,13,11,0.76)] p-4 shadow-[0_24px_80px_rgba(0,0,0,0.44)] backdrop-blur-2xl'>
      <div className='flex items-start justify-between gap-3'>
        <div>
          <p className='text-[11px] uppercase tracking-[0.32em] text-[#d4b15d]'>
            SALAMATSYZBY, {(user?.full_name || 'Aybek').toUpperCase()}
          </p>
          <h1 className='font-display mt-3 text-[2.7rem] leading-[0.92] text-[#f7efe3]'>
            Карта слышит путь.
          </h1>
          <p className='mt-2 text-sm text-white/56'>
            Реальный маршрут по дорогам и тропам. Если дальше только пешком, это будет видно пунктиром.
          </p>
        </div>

        <div className='flex items-center gap-2'>
          <button
            type='button'
            onClick={() => setSettingsOpen((current) => !current)}
            className='rounded-[22px] border border-white/10 bg-white/6 p-3 text-white/82'
          >
            <Settings2 size={18} />
          </button>
          <button
            type='button'
            onClick={logout}
            className='rounded-[22px] border border-white/10 bg-white/6 p-3 text-white/82'
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>

      <div className='mt-4 flex items-center gap-2 rounded-[24px] border border-white/10 bg-black/26 px-4 py-3'>
        <Search size={16} className='text-white/40' />
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder='Искать место, регион или традицию'
          className='w-full border-none bg-transparent text-sm text-[#f7efe3] outline-none placeholder:text-white/36'
        />
        <button
          type='button'
          onClick={() => setFiltersOpen((current) => !current)}
          className='rounded-full border border-white/10 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#d8af58]'
        >
          Фильтр
        </button>
      </div>

      <AnimatePresence>
        {settingsOpen && (
          <Motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className='mt-4 rounded-[26px] border border-white/10 bg-black/24 p-4'
          >
            <div className='flex items-center justify-between gap-3'>
              <div>
                <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>Тема</p>
                <p className='mt-1 text-sm text-[#f7efe3]'>Меняет карту и весь свет сцены</p>
              </div>
              <div className='flex gap-2'>
                <FilterChip
                  label='Ночь'
                  active={settings.theme === 'night'}
                  accent='#ffb366'
                  onClick={() => updateSettings({ theme: 'night' })}
                />
                <FilterChip
                  label='Рассвет'
                  active={settings.theme === 'dawn'}
                  accent='#ffe3a6'
                  onClick={() => updateSettings({ theme: 'dawn' })}
                />
              </div>
            </div>

            <div className='mt-4 flex items-center justify-between gap-3 rounded-[20px] border border-white/10 bg-white/4 px-4 py-3'>
              <div>
                <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>AI-озвучка</p>
                <p className='mt-1 text-sm text-[#f7efe3]'>
                  {settings.voiceEnabled ? 'Включена' : 'Выключена'}
                </p>
                {selectedVoiceName ? (
                  <p className='mt-1 text-xs text-white/42'>Голос: {selectedVoiceName}</p>
                ) : null}
              </div>
              <button
                type='button'
                onClick={() => updateSettings({ voiceEnabled: !settings.voiceEnabled })}
                className={`rounded-full border px-4 py-2 text-sm font-semibold ${
                  settings.voiceEnabled
                    ? 'border-[#ff7b37]/40 bg-[#ff7b37]/16 text-[#fef1e6]'
                    : 'border-white/10 bg-white/5 text-white/72'
                }`}
              >
                {settings.voiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
              </button>
            </div>
          </Motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {filtersOpen && (
          <Motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className='mt-4 rounded-[26px] border border-white/10 bg-black/24 p-4'
          >
            <div className='flex items-start justify-between gap-3'>
              <div>
                <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>Типы точек</p>
                <div className='mt-3 flex flex-wrap gap-2'>
                  {Object.entries(KIND_META).map(([key, value]) => (
                    <FilterChip
                      key={key}
                      label={value.label}
                      active={kindFilter === key}
                      accent={value.accent}
                      onClick={() => setKindFilter(key)}
                    />
                  ))}
                </div>
              </div>
              <button
                type='button'
                onClick={() => setFiltersOpen(false)}
                className='rounded-full border border-white/10 p-2 text-white/72'
              >
                <X size={14} />
              </button>
            </div>

            <div className='mt-4'>
              <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>Рельеф</p>
              <div className='mt-3 flex flex-wrap gap-2'>
                {Object.entries(TERRAIN_FILTERS).map(([key, label]) => (
                  <FilterChip
                    key={key}
                    label={label}
                    active={terrainFilter === key}
                    accent='#d8af58'
                    onClick={() => setTerrainFilter(key)}
                  />
                ))}
              </div>
            </div>

            <div className='mt-4 flex items-center justify-between gap-3 rounded-[20px] border border-white/10 bg-white/4 px-4 py-3'>
              <div>
                <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>Только точные точки</p>
                <p className='mt-1 text-sm text-[#f7efe3]'>Оставляет только проверенные координаты</p>
              </div>
              <button
                type='button'
                onClick={() => setVerifiedOnly((current) => !current)}
                className={`rounded-full border px-4 py-2 text-sm font-semibold ${
                  verifiedOnly
                    ? 'border-[#ff7b37]/40 bg-[#ff7b37]/16 text-[#fef1e6]'
                    : 'border-white/10 bg-white/5 text-white/72'
                }`}
              >
                {verifiedOnly ? 'Да' : 'Нет'}
              </button>
            </div>
          </Motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

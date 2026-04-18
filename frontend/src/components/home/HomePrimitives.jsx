import { KIND_META, PANEL_TABS, TERRAIN_FILTERS, TRANSPORTS, formatDistance, seasonalityLabel } from '@/components/home/home-utils'

export function FilterChip({ label, active, onClick, accent = '#f7efe3' }) {
  return (
    <button
      type='button'
      onClick={onClick}
      className={`rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
        active ? 'text-[#1c120e]' : 'text-white/78'
      }`}
      style={{
        borderColor: active ? `${accent}88` : 'rgba(255,255,255,0.12)',
        background: active ? accent : 'rgba(255,255,255,0.04)',
      }}
    >
      {label}
    </button>
  )
}

export function MetricCard({ label, value, highlight = false }) {
  return (
    <div className={`rounded-[24px] border px-3 py-3 ${highlight ? 'border-[#ff7b37]/40 bg-[#ff7b37]/10' : 'border-white/10 bg-white/5'}`}>
      <p className='text-[11px] uppercase tracking-[0.2em] text-white/46'>{label}</p>
      <p className='mt-2 text-lg font-semibold text-[#f7efe3]'>{value}</p>
    </div>
  )
}

export function TransportButton({ id, active, onClick }) {
  const Icon = TRANSPORTS[id].icon

  return (
    <button
      type='button'
      onClick={() => onClick(id)}
      className={`rounded-2xl border px-3 py-2.5 text-sm font-semibold transition ${
        active
          ? 'border-[#ff7b37]/70 bg-[#ff7b37]/16 text-[#fef1e6]'
          : 'border-white/10 bg-white/5 text-white/70'
      }`}
    >
      <span className='flex items-center gap-2'>
        <Icon size={16} />
        {TRANSPORTS[id].label}
      </span>
    </button>
  )
}

export function PanelTabButton({ tabId, active, onClick }) {
  const Icon = PANEL_TABS[tabId].icon

  return (
    <button
      type='button'
      onClick={() => onClick(tabId)}
      className={`flex min-w-0 flex-1 items-center justify-center gap-2 rounded-2xl border px-3 py-2.5 text-sm font-semibold transition ${
        active
          ? 'border-[#ff7b37]/40 bg-[#ff7b37]/12 text-[#fff1e5]'
          : 'border-white/10 bg-white/5 text-white/68'
      }`}
    >
      <Icon size={16} />
      <span className='truncate'>{PANEL_TABS[tabId].label}</span>
    </button>
  )
}

export function LocationCard({ location, active, onClick, variant = 'carousel' }) {
  const Icon = KIND_META[location.kind]?.icon || KIND_META.petroglyph.icon

  return (
    <button
      type='button'
      onClick={() => onClick(location)}
      className={`overflow-hidden rounded-[28px] border text-left transition ${
        variant === 'list' ? 'w-full' : 'w-[214px] shrink-0'
      } ${
        active
          ? 'border-[#ff7b37]/40 bg-[#221710]'
          : 'border-white/10 bg-[rgba(255,255,255,0.04)]'
      }`}
    >
      <div
        className={`bg-cover bg-center ${variant === 'list' ? 'h-28' : 'h-32'}`}
        style={{
          backgroundImage: location.image_url
            ? `linear-gradient(180deg, rgba(18,12,10,0.06), rgba(18,12,10,0.86)), url(${location.image_url})`
            : 'linear-gradient(135deg, rgba(228,146,64,0.34), rgba(16,12,11,0.9))',
        }}
      />
      <div className='space-y-2 p-4'>
        <div className='flex items-center justify-between gap-3'>
          <span className='inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[#d8af58]'>
            <Icon size={14} />
            {KIND_META[location.kind]?.label || 'Точка'}
          </span>
          <span className='text-[11px] text-white/50'>{seasonalityLabel(location.seasonality)}</span>
        </div>
        <h3 className='font-display text-[1.75rem] leading-none text-[#f7efe3]'>{location.name}</h3>
        <p className='text-sm text-white/64'>{location.region}</p>
        <div className='flex items-center justify-between gap-3 text-xs text-white/56'>
          <span>{location.route_available ? 'Маршрут доступен' : 'Только карточка'}</span>
          {location.straightDistanceM ? <span>{formatDistance(location.straightDistanceM)}</span> : null}
        </div>
        {variant === 'list' && (
          <div className='flex items-center justify-between gap-3 text-xs text-white/44'>
            <span>{TERRAIN_FILTERS[location.terrain] || location.terrain}</span>
            <span>{location.coordinate_quality === 'verified' ? 'Проверено' : 'Координаты уточняются'}</span>
          </div>
        )}
      </div>
    </button>
  )
}

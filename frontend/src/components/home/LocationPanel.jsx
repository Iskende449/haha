import { FilterChip, MetricCard } from '@/components/home/HomePrimitives'
import { KIND_META, TERRAIN_FILTERS, formatDistance, qualityLabel, seasonalityLabel } from '@/components/home/home-utils'

export function LocationPanel({ activeLocation }) {
  if (!activeLocation) {
    return (
      <div className='rounded-[26px] border border-white/10 bg-white/4 px-4 py-6 text-sm text-white/62'>
        Выберите точку на карте или из списка, чтобы посмотреть детали и построить маршрут.
      </div>
    )
  }

  const selectedKind = KIND_META[activeLocation.kind || 'petroglyph'] || KIND_META.petroglyph

  return (
    <div className='overflow-hidden rounded-[30px] border border-white/10 bg-[rgba(255,255,255,0.04)]'>
      <div
        className='h-40 bg-cover bg-center'
        style={{
          backgroundImage: activeLocation.image_url
            ? `linear-gradient(180deg, rgba(16,10,9,0.16), rgba(16,10,9,0.86)), url(${activeLocation.image_url})`
            : 'linear-gradient(135deg, rgba(228,146,64,0.36), rgba(15,11,10,0.92))',
        }}
      />

      <div className='space-y-4 p-4'>
        <div className='flex items-start justify-between gap-3'>
          <div>
            <p className='text-[11px] uppercase tracking-[0.2em] text-[#d8af58]'>
              {selectedKind.label}
            </p>
            <h2 className='font-display mt-2 text-[2.1rem] leading-none text-[#f7efe3]'>
              {activeLocation.name}
            </h2>
            <p className='mt-2 text-sm text-white/62'>{activeLocation.region}</p>
          </div>

          <span className='rounded-full border border-white/10 bg-black/18 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-white/74'>
            {qualityLabel(activeLocation.coordinate_quality)}
          </span>
        </div>

        <p className='text-sm leading-6 text-white/78'>{activeLocation.summary}</p>

        <div className='flex flex-wrap gap-2'>
          <FilterChip label={seasonalityLabel(activeLocation.seasonality)} active accent='#d8af58' onClick={() => {}} />
          <FilterChip
            label={TERRAIN_FILTERS[activeLocation.terrain] || activeLocation.terrain}
            active
            accent='#ffcf8a'
            onClick={() => {}}
          />
          {activeLocation.travel_tags?.slice(0, 3).map((tag) => (
            <FilterChip key={tag} label={tag} active accent='#f7efe3' onClick={() => {}} />
          ))}
        </div>

        <div className='grid grid-cols-2 gap-2'>
          <MetricCard
            label='От вас'
            value={activeLocation.straightDistanceM ? formatDistance(activeLocation.straightDistanceM) : '...'}
          />
          <MetricCard
            label='Маршрут'
            value={activeLocation.route_available ? 'Построение доступно' : 'Нет координат'}
          />
        </div>

        {activeLocation.archaeological_description ? (
          <div className='rounded-[22px] border border-white/10 bg-black/18 p-4'>
            <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>Контекст места</p>
            <p className='mt-2 text-sm leading-6 text-white/74'>{activeLocation.archaeological_description}</p>
          </div>
        ) : null}
      </div>
    </div>
  )
}

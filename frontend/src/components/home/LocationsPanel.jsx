import { LocationCard } from '@/components/home/HomePrimitives'

export function LocationsPanel({ locations, selectedId, onSelectLocation }) {
  if (!locations.length) {
    return (
      <div className='rounded-[26px] border border-white/10 bg-white/4 px-4 py-6 text-center text-sm text-white/58'>
        По текущим фильтрам ничего не найдено.
      </div>
    )
  }

  return (
    <div className='space-y-3'>
      <div className='flex items-center justify-between gap-3'>
        <div>
          <p className='text-[11px] uppercase tracking-[0.2em] text-[#d8af58]'>Выбор направления</p>
          <p className='mt-1 text-sm text-white/56'>Список вынесен отдельно, чтобы не забивать карту и маршруты.</p>
        </div>
        <span className='rounded-full border border-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-white/54'>
          {locations.length} точек
        </span>
      </div>

      {locations.map((location) => (
        <LocationCard
          key={location.source_id}
          location={location}
          active={location.source_id === selectedId}
          onClick={onSelectLocation}
          variant='list'
        />
      ))}
    </div>
  )
}

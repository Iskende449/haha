import { useMemo } from 'react'
import { AlertTriangle, Clock3, MapPinned, Navigation, Volume2, VolumeX } from 'lucide-react'

import { MetricCard, TransportButton } from '@/components/home/HomePrimitives'
import {
  SMART_ROUTE_META,
  TERRAIN_FILTERS,
  TRANSPORTS,
  TRANSPORT_ACCENTS,
  buildRouteBreakdown,
  formatDistance,
  formatDuration,
  providerLabel,
  segmentTitle,
  trafficLabel,
} from '@/components/home/home-utils'

function LegendRow({ color, dashed = false, title, description }) {
  return (
    <div className='flex items-start gap-3 rounded-[20px] border border-white/8 bg-black/14 px-3 py-3'>
      <div className='pt-2'>
        <div
          className='w-12 border-b-[4px]'
          style={{
            borderColor: color,
            borderStyle: dashed ? 'dashed' : 'solid',
            opacity: dashed ? 0.92 : 1,
          }}
        />
      </div>
      <div>
        <p className='text-sm font-semibold text-[#f7efe3]'>{title}</p>
        <p className='mt-1 text-xs leading-5 text-white/54'>{description}</p>
      </div>
    </div>
  )
}

export function RoutePanel({
  routeData,
  routeError,
  transport,
  setTransport,
  activeLocation,
  onBuildRoute,
  isLoading,
  settings,
  speak,
  isSupported,
}) {
  const accent = TRANSPORT_ACCENTS[transport] || TRANSPORT_ACCENTS.car
  const routeBreakdown = useMemo(
    () => buildRouteBreakdown(routeData?.route_geometry, routeData?.transport_mode || transport),
    [routeData, transport],
  )

  return (
    <div className='space-y-4'>
      {routeData ? (
        <div className='rounded-[28px] border border-[#ff7b37]/20 bg-[linear-gradient(180deg,rgba(255,124,56,0.14),rgba(255,255,255,0.04))] p-4'>
          <div className='flex items-start justify-between gap-3'>
            <div>
              <p className='text-[11px] uppercase tracking-[0.2em] text-[#d8af58]'>Реальный маршрут</p>
              <h2 className='font-display mt-2 text-[2rem] leading-none text-[#f7efe3]'>
                {routeData.location?.name}
              </h2>
            </div>
            <span className='rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-white/74'>
              {trafficLabel(routeData.traffic?.level)}
            </span>
          </div>

          <div className='mt-4 grid grid-cols-2 gap-2'>
            <MetricCard label='ETA' value={formatDuration(routeData.duration_s)} highlight />
            <MetricCard label='Дистанция' value={formatDistance(routeData.distance_m)} />
            <MetricCard label='Задержка' value={`${routeData.traffic_delay_minutes || 0} мин`} />
            <MetricCard label='Провайдер' value={providerLabel(routeData.provider)} />
          </div>

          <div className='mt-4 rounded-[22px] border border-white/10 bg-black/18 p-4'>
            <div className='flex items-start justify-between gap-3'>
              <div>
                <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>AI-анализ</p>
                <p className='mt-2 text-sm leading-6 text-white/78'>{routeData.analysis}</p>
              </div>
              {isSupported ? (
                <button
                  type='button'
                  onClick={() => speak(routeData.voice_script)}
                  className='rounded-full border border-white/10 bg-white/5 p-2 text-white/84'
                >
                  {settings.voiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
                </button>
              ) : null}
            </div>
          </div>

          {routeBreakdown.segments.length > 0 ? (
            <div className='mt-4 rounded-[22px] border border-white/10 bg-black/18 p-4'>
              <p className='text-[11px] uppercase tracking-[0.18em] text-white/46'>Разбор пути</p>
              <div className='mt-3 space-y-2'>
                {routeBreakdown.segments.map((segment) => (
                  <div key={segment.id} className='flex items-center justify-between gap-3 rounded-[18px] border border-white/8 bg-white/4 px-3 py-3'>
                    <div>
                      <p className='text-sm font-semibold text-[#f7efe3]'>{segmentTitle(segment)}</p>
                      <p className='mt-1 text-xs leading-5 text-white/50'>
                        {segment.kind === 'walk_connector'
                          ? segment.transport_context === 'foot'
                            ? 'Это часть пешего маршрута, найденная как продолжение walking-сети.'
                            : 'Пунктиром показан пеший добор после окончания доступной сети текущего режима.'
                          : segment.kind === 'approximation'
                            ? 'Сеть дорог недоступна, поэтому отрезок показан приблизительно.'
                            : segment.transport_context === 'foot'
                              ? 'Сплошная линия идёт по найденной walking-сети и доступным пешим проходам.'
                              : segment.transport_context === 'bike'
                                ? 'Сплошная линия идёт по сети, где маршрут допускает движение на велосипеде.'
                                : 'Сплошная линия идёт по доступной дорожной сети для автомобиля.'}
                      </p>
                    </div>
                    <span className='text-sm font-semibold text-[#ffe2cb]'>{formatDistance(segment.distance_m)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className='mt-4 grid gap-2'>
            <LegendRow
              color={accent}
              title='Сплошная линия'
              description={
                routeData.transport_mode === 'foot'
                  ? 'Для пешего режима весь найденный путь показывается одной сплошной линией.'
                  : 'Основной участок маршрута по реальной дороге, тропе или проходимой сети.'
              }
            />
            {routeData.transport_mode !== 'foot' ? (
              <LegendRow
                color={routeData.transport_mode === 'bike' ? '#b9f5d9' : '#ffd6b8'}
                dashed
                title='Пунктир'
                description='Дальше текущий режим больше не проходит. Этот кусок нужно пройти пешком.'
              />
            ) : null}
          </div>

          {routeData.steps?.length > 0 ? (
            <div className='mt-4 space-y-2'>
              {routeData.steps.slice(0, 4).map((step, index) => (
                <div key={`${step.instruction}-${index}`} className='rounded-[20px] border border-white/8 bg-black/18 px-4 py-3'>
                  <p className='text-[11px] uppercase tracking-[0.18em] text-white/40'>Шаг {index + 1}</p>
                  <p className='mt-1 text-sm text-[#f7efe3]'>{step.instruction}</p>
                  <p className='mt-2 text-xs text-white/44'>
                    {formatDistance(step.distance_m)} • {formatDuration(step.duration_s)}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {routeError ? (
        <div className='rounded-[22px] border border-[#ff7b37]/24 bg-[#ff7b37]/10 px-4 py-3 text-sm text-[#ffd5bf]'>
          <div className='flex items-start gap-2'>
            <AlertTriangle size={16} className='mt-0.5 shrink-0' />
            <span>{routeError}</span>
          </div>
        </div>
      ) : null}

      <div className='rounded-[26px] border border-white/10 bg-[rgba(255,255,255,0.04)] p-4'>
        <div className='flex items-center justify-between gap-3'>
          <div>
            <p className='text-[11px] uppercase tracking-[0.2em] text-white/42'>Режим маршрута</p>
            <h3 className='mt-1 text-base font-semibold text-[#f7efe3]'>Отдельно для авто, вело и пешком</h3>
          </div>
          {activeLocation ? (
            <span className='rounded-full border border-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-white/54'>
              {activeLocation.route_available ? 'Точка готова' : 'Нет координат'}
            </span>
          ) : null}
        </div>

        <div className='mt-3 flex flex-wrap gap-2'>
          {Object.keys(TRANSPORTS).map((key) => (
            <TransportButton key={key} id={key} active={transport === key} onClick={setTransport} />
          ))}
        </div>

        <div className='mt-3 rounded-[22px] border border-[#ff7b37]/20 bg-[#ff7b37]/10 px-4 py-4'>
          <p className='font-semibold text-[#f7efe3]'>{SMART_ROUTE_META.title}</p>
          <p className='mt-2 text-sm leading-6 text-white/62'>{SMART_ROUTE_META.description}</p>
        </div>

        <button
          type='button'
          onClick={onBuildRoute}
          disabled={!activeLocation?.route_available || isLoading}
          className='mt-5 flex w-full items-center justify-center gap-3 rounded-[26px] border border-[#ff7b37]/30 bg-[linear-gradient(180deg,#ff8a4a,#e55b21)] px-5 py-4 text-base font-semibold text-[#fff4eb] shadow-[0_20px_60px_rgba(229,91,33,0.38)] transition disabled:cursor-not-allowed disabled:opacity-50'
        >
          <Navigation size={18} />
          {isLoading ? 'Считаю реальный маршрут...' : 'Построить маршрут'}
        </button>

        <p className='mt-3 text-center text-xs leading-5 text-white/44'>
          Сначала рисуется проходимая дорога или тропа, а недоступный хвост для авто и велосипеда отмечается пунктиром как пеший добор.
        </p>

        {activeLocation ? (
          <div className='mt-4 flex items-center justify-center gap-4 text-xs text-white/46'>
            <span className='inline-flex items-center gap-1'>
              <MapPinned size={13} />
              {activeLocation.name}
            </span>
            <span className='inline-flex items-center gap-1'>
              <Clock3 size={13} />
              {routeData ? formatDuration(routeData.duration_s) : 'ETA после построения'}
            </span>
            <span className='inline-flex items-center gap-1'>
              <Navigation size={13} />
              {TERRAIN_FILTERS[activeLocation.terrain] || activeLocation.terrain}
            </span>
          </div>
        ) : null}
      </div>
    </div>
  )
}

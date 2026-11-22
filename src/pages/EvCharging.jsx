import BarChart from '../components/charts/BarChart'
import ChartCard from '../components/charts/ChartCard'
import LineChart from '../components/charts/LineChart'
import MapPlaceholder from '../components/MapPlaceholder'
import { Card, ErrorState } from '../components/ui/Card'
import { BoltIcon, ChevronDownIcon, ParkingIcon } from '../components/ui/Icons'
import LocateButton from '../components/ui/LocateButton'
import ScrollHint from '../components/ui/ScrollHint'
import { ListSkeleton } from '../components/ui/Skeleton'
import { useApi } from '../hooks/useApi'
import { useState } from 'react'
import { useMapFocus } from '../hooks/useMapFocus'
import { useUserLocation } from '../hooks/useUserLocation'
import { useLang } from '../i18n/LanguageContext'
import { api } from '../services/api'
import { distanceM } from '../utils/transit'

const TWO_MIN = 2 * 60 * 1000
const TOP = 12 // bar chart: a few hundred real chargers would be unreadable
const MAP_TOP = 5 // map chips: keep the map itself uncluttered
const NEAREST = 3 // shown at once; the rest open with the arrow
const PARKING_COLOR = '#2563eb'
const SYNTAGMA = { lat: 37.9755, lng: 23.7348 }

// Status → color + translation key
export const EV_STATUS = {
  available: { color: '#22c55e', key: 'ev.open' },
  busy: { color: '#f97316', key: 'ev.busy' },
  offline: { color: '#94a3b8', key: 'ev.offline' },
}

// The arrow next to a card's title: opens the rest of the list beyond the NEAREST
function MoreToggle({ open, onToggle, rest }) {
  const { t } = useLang()
  if (rest <= 0) return null
  return (
    <button
      onClick={onToggle}
      aria-expanded={open}
      className="ms-2 inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 align-middle text-xs font-semibold text-primary-dark transition hover:bg-primary/20 dark:text-primary-light"
    >
      {open ? t('common.showLess') : t('common.showMore', { n: rest })}
      <ChevronDownIcon className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`} />
    </button>
  )
}

export default function EvCharging() {
  const { t, lang, locale } = useLang()
  const stations = useApi(api.getEvStations, [lang], { refreshMs: TWO_MIN })
  const usage = useApi(api.getEvUsage, [], { refreshMs: TWO_MIN })
  const parking = useApi(api.getParking, [])
  const { pos } = useUserLocation()
  const { mapRef, focus, focusOn, clearFocus } = useMapFocus()
  const [evOpen, setEvOpen] = useState(false)
  const [lotsOpen, setLotsOpen] = useState(false)

  const list = [...(stations.data ?? [])].sort((a, b) => b.available - a.available)
  const top = list.slice(0, TOP)
  const freeNow = list.reduce((a, s) => a + s.available, 0)
  const origin = pos ?? SYNTAGMA
  const nearEv = list.map((s) => ({ ...s, dist: distanceM(origin, s) })).sort((a, b) => a.dist - b.dist)
  const lots = (parking.data ?? []).map((p) => ({ ...p, dist: distanceM(origin, p) })).sort((a, b) => a.dist - b.dist)
  const lotName = (p) => (lang === 'el' ? p.name : p.name_en || p.name) || t(`parking.type.${p.type}`)
  const formatDist = (m) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`)
  const euro = (v) => new Intl.NumberFormat(locale, { style: 'currency', currency: 'EUR', minimumFractionDigits: 2 }).format(v)

  return (
    <div className="space-y-4">
      <MapPlaceholder
        ref={mapRef}
        focus={focus}
        onClearFocus={clearFocus}
        loadingData={stations.loading}
        chips={top.map((s) => ({
          id: s.id,
          lat: s.lat,
          lng: s.lng,
          label: `${s.name} · ${s.available}/${s.total}`,
          color: EV_STATUS[s.status].color,
          title: t(EV_STATUS[s.status].key),
        })).concat(
          lots.map((p) => ({ id: p.id, lat: p.lat, lng: p.lng, label: `P · ${lotName(p)}`, color: PARKING_COLOR, title: t('parking.title') })),
        ).slice(0, MAP_TOP)}
        overlay={
          <div>
            <p className="text-xs text-muted">{t('ev.title')}</p>
            <p className="flex items-baseline gap-1.5">
              <BoltIcon className="h-4 w-4 self-center text-primary" />
              <span className="text-xl font-bold text-ink sm:text-2xl">{freeNow}</span>
              <span className="text-xs text-muted">
                {t('ev.summaryFree')} · {list.length} {t('ev.summaryStations')}
              </span>
            </p>
          </div>
        }
      />

      <h1 className="font-display text-xl font-bold tracking-tight sm:text-2xl bg-gradient-to-r from-primary-darker via-violet-600 to-fuchsia-500 bg-clip-text text-transparent dark:from-primary-light dark:via-violet-400 dark:to-fuchsia-400">{t('ev.title')}</h1>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title={t('ev.free')} query={stations}>
          {() => (
            <BarChart
              label={t('ev.available')}
              // real charger names are long: 12 full names overlap on the axis
              labels={top.map((s) => (s.name.length > 16 ? `${s.name.slice(0, 15)}…` : s.name))}
              values={top.map((s) => s.available)}
              colors={top.map((s) => EV_STATUS[s.status].color)}
              integer
            />
          )}
        </ChartCard>

        {/* the backend's own 10-minute samples: the curve fills in over the day */}
        <ChartCard title={t('ev.occupancy')} query={usage}>
          {(rows) =>
            rows.length < 2 ? (
              <p className="flex h-full items-center justify-center px-6 text-center text-sm text-muted">{t('ev.collecting')}</p>
            ) : (
              <LineChart series={[{ name: t('series.today'), data: rows.map((r) => ({ x: r.time, y: r.occupancy })) }]} />
            )
          }
        </ChartCard>
      </div>

      <Card
        title={<>{t('ev.list')}<MoreToggle open={evOpen} onToggle={() => setEvOpen((v) => !v)} rest={nearEv.length - NEAREST} /></>}
        bodyClassName="px-3 py-1 sm:px-4">
        {stations.loading ? (
          <div className="py-3">
            <ListSkeleton rows={4} />
          </div>
        ) : stations.error ? (
          <ErrorState error={stations.error} onRetry={stations.reload} />
        ) : (
          <ul className="divide-y divide-line">
            {(evOpen ? nearEv : nearEv.slice(0, NEAREST)).map((s) => {
              const status = EV_STATUS[s.status]
              return (
                <li key={s.id} className="flex items-center gap-3 py-3">
                  <span
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white"
                    style={{ background: status.color }}
                    title={t(status.key)}
                  >
                    <BoltIcon className="h-5 w-5" />
                  </span>

                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-ink">{s.name}</p>
                    <p className="truncate text-sm text-muted">{[s.address, formatDist(s.dist)].filter(Boolean).join(' · ')}</p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                      <span className="rounded-full px-2 py-0.5 font-semibold" style={{ background: `${status.color}26`, color: status.color }}>
                        {s.status === 'offline' ? t(status.key) : `${s.available}/${s.total} ${t('ev.available')}`}
                      </span>
                      {s.powerKw != null && <span className="rounded-full bg-primary/10 px-2 py-0.5 text-primary-dark dark:text-primary-light">{s.powerKw} kW</span>}
                      {s.pricePerKwh != null && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">{euro(s.pricePerKwh)}/kWh</span>}
                      <span className="text-muted">{s.connectors.join(' · ')}</span>
                    </div>
                  </div>

                  <LocateButton
                    active={focus?.id === s.id}
                    onClick={() => focusOn({ id: s.id, lat: s.lat, lng: s.lng, label: `EV · ${s.name}, ${s.address}` })}
                  />
                </li>
              )
            })}
          </ul>
        )}
      </Card>

      <Card
        title={<>{t('parking.title')}<MoreToggle open={lotsOpen} onToggle={() => setLotsOpen((v) => !v)} rest={lots.length - NEAREST} /></>}
        bodyClassName="px-3 py-1 sm:px-4">
        {parking.loading ? (
          <div className="py-3">
            <ListSkeleton rows={4} />
          </div>
        ) : parking.error ? (
          <ErrorState error={parking.error} onRetry={parking.reload} />
        ) : (
          <ul className="divide-y divide-line">
            {(lotsOpen ? lots : lots.slice(0, NEAREST)).map((p) => (
              <li key={p.id} className="flex items-center gap-3 py-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white" style={{ background: PARKING_COLOR }}>
                  <ParkingIcon className="h-5 w-5" />
                </span>

                <div className="min-w-0 flex-1">
                  <p className="font-medium text-ink">{lotName(p)}</p>
                  <p className="truncate text-sm text-muted">{[p.address, formatDist(p.dist)].filter(Boolean).join(' · ')}</p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                    <span className="rounded-full bg-primary/10 px-2 py-0.5 text-primary-dark dark:text-primary-light">{t(`parking.type.${p.type}`)}</span>
                    {p.capacity != null && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">{t('parking.spaces', { n: p.capacity })}</span>}
                    {p.ev_points != null && (
                      <span className="rounded-full px-2 py-0.5 font-semibold" style={{ background: `${EV_STATUS.available.color}26`, color: EV_STATUS.available.color }}>
                        {t('parking.ev', { n: p.ev_points })}
                      </span>
                    )}
                    {p.hours === '24/7' && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">24/7</span>}
                    {p.fee === false && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">{t('parking.free')}</span>}
                    {p.wheelchair && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">{t('parking.accessible')}</span>}
                    {p.park_ride && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">{t('parking.parkRide')}</span>}
                  </div>
                </div>

                <LocateButton
                  active={focus?.id === p.id}
                  onClick={() => focusOn({ id: p.id, lat: p.lat, lng: p.lng, label: `P · ${lotName(p)}` })}
                />
              </li>
            ))}
          </ul>
        )}
        <p className="pb-2 text-[11px] text-muted">{t('parking.source')}</p>
      </Card>

      <ScrollHint />
    </div>
  )
}

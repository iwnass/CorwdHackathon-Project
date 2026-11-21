import BarChart from '../components/charts/BarChart'
import ChartCard from '../components/charts/ChartCard'
import LineChart from '../components/charts/LineChart'
import MapPlaceholder from '../components/MapPlaceholder'
import { Card, ErrorState } from '../components/ui/Card'
import { BoltIcon } from '../components/ui/Icons'
import LocateButton from '../components/ui/LocateButton'
import ScrollHint from '../components/ui/ScrollHint'
import { ListSkeleton } from '../components/ui/Skeleton'
import { useApi } from '../hooks/useApi'
import { useMapFocus } from '../hooks/useMapFocus'
import { useLang } from '../i18n/LanguageContext'
import { api } from '../services/api'

const TWO_MIN = 2 * 60 * 1000
const TOP = 12 // chips and bar chart: a few hundred real chargers would be unreadable
const hh = (h) => `${String(h).padStart(2, '0')}:00`

// Status → color + translation key
export const EV_STATUS = {
  available: { color: '#22c55e', key: 'ev.open' },
  busy: { color: '#f97316', key: 'ev.busy' },
  offline: { color: '#94a3b8', key: 'ev.offline' },
}

export default function EvCharging() {
  const { t, lang, locale } = useLang()
  const stations = useApi(api.getEvStations, [lang], { refreshMs: TWO_MIN })
  const usage = useApi(api.getEvUsage, [lang])
  const { mapRef, focus, focusOn, clearFocus } = useMapFocus()

  const list = [...(stations.data ?? [])].sort((a, b) => b.available - a.available)
  const top = list.slice(0, TOP)
  const freeNow = list.reduce((a, s) => a + s.available, 0)
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
        }))}
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

      <h1 className="text-lg font-semibold text-ink">{t('ev.title')}</h1>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title={t('ev.free')} query={stations}>
          {() => (
            <BarChart
              label={t('ev.available')}
              labels={top.map((s) => s.name)}
              values={top.map((s) => s.available)}
              colors={top.map((s) => EV_STATUS[s.status].color)}
              integer
            />
          )}
        </ChartCard>

        <ChartCard title={t('ev.occupancy')} query={usage}>
          {(rows) => (
            <LineChart
              datetime={false}
              series={[
                { name: t('series.today'), data: rows.map((r) => ({ x: hh(r.hour), y: r.occupancy })) },
                { name: t('series.typical'), data: rows.map((r) => ({ x: hh(r.hour), y: r.typical })) },
              ].filter((s) => s.data.some((p) => p.y != null))}
            />
          )}
        </ChartCard>
      </div>

      <Card title={t('ev.list')} bodyClassName="px-3 py-1 sm:px-4">
        {stations.loading ? (
          <div className="py-3">
            <ListSkeleton rows={4} />
          </div>
        ) : stations.error ? (
          <ErrorState error={stations.error} onRetry={stations.reload} />
        ) : (
          <ul className="divide-y divide-line">
            {list.map((s) => {
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
                    <p className="truncate text-sm text-muted">{s.address}</p>
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

      <ScrollHint />
    </div>
  )
}

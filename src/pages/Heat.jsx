import { useMemo } from 'react'
import BarChart from '../components/charts/BarChart'
import ChartCard from '../components/charts/ChartCard'
import LineChart from '../components/charts/LineChart'
import MapPlaceholder from '../components/MapPlaceholder'
import { Card, ErrorState } from '../components/ui/Card'
import { SunIcon } from '../components/ui/Icons'
import LocateButton from '../components/ui/LocateButton'
import ScrollHint from '../components/ui/ScrollHint'
import { ListSkeleton } from '../components/ui/Skeleton'
import { useApi } from '../hooks/useApi'
import { useMapFocus } from '../hooks/useMapFocus'
import { useUserLocation } from '../hooks/useUserLocation'
import { useTheme } from '../context/ThemeContext'
import { useLang } from '../i18n/LanguageContext'
import { api } from '../services/api'
import { distanceM } from '../utils/transit'

const SYNTAGMA = { lat: 37.9755, lng: 23.7348 }
const TEN_MIN = 10 * 60 * 1000
// NWS heat-index levels from the backend → colour
const LEVEL = { none: '#22c55e', caution: '#eab308', extreme_caution: '#f97316', danger: '#ef4444', extreme_danger: '#7f1d1d' }
const COOL = ['fountain', 'pocket_park', 'pool']

export default function Heat() {
  const { t, lang } = useLang()
  const heat = useApi(api.getHeat, [], { refreshMs: TEN_MIN })
  const places = useApi(api.getPlaces, [])
  const { pos } = useUserLocation()
  const { showHeatmap } = useTheme()
  const { mapRef, focus, focusOn, clearFocus } = useMapFocus()

  const origin = pos ?? SYNTAGMA
  const cool = useMemo(
    () =>
      (places.data ?? [])
        .filter((p) => COOL.includes(p.kind))
        .map((p) => ({ ...p, dist: distanceM(origin, p) }))
        .sort((a, b) => a.dist - b.dist)
        .slice(0, 8),
    [places.data, origin],
  )
  const city = heat.data?.city
  const formatDist = (m) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`)
  const name = (p) => (lang === 'el' ? p.name : p.name_en || p.name)

  return (
    <div className="space-y-4">
      <MapPlaceholder
        ref={mapRef}
        center={pos ?? undefined}
        focus={focus}
        onClearFocus={clearFocus}
        loadingData={heat.loading}
        chips={showHeatmap ? cool.map((p, i) => ({ id: `cool-${i}`, lat: p.lat, lng: p.lng, label: `${t(`kind.${p.kind}`)} · ${formatDist(p.dist)}`, color: '#0ea5e9' })) : []}
        overlay={
          showHeatmap && city && (
            <div>
              <p className="text-xs text-muted">{t('heat.now')}</p>
              <p className="flex items-baseline gap-1.5">
                <SunIcon className="h-4 w-4 self-center" style={{ color: LEVEL[city.heat_level] }} />
                <span className="text-xl font-bold text-ink sm:text-2xl">{Math.round(city.temperature_avg)}°C</span>
                <span className="text-xs text-muted">
                  {t('heat.feels', { n: Math.round(city.feels_like_avg) })} · {t(`heat.level.${city.heat_level}`)}
                </span>
              </p>
            </div>
          )
        }
      />

      <h1 className="font-display text-xl font-bold tracking-tight sm:text-2xl bg-gradient-to-r from-primary-darker via-violet-600 to-fuchsia-500 bg-clip-text text-transparent dark:from-primary-light dark:via-violet-400 dark:to-fuchsia-400">{t('heat.title')}</h1>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title={t('heat.today')} query={heat}>
          {(d) => (
            <LineChart
              series={[
                { name: t('heat.temperature'), data: d.hourly.map((h) => ({ x: h.time, y: h.temperature_avg })) },
                { name: t('heat.feelsLike'), data: d.hourly.map((h) => ({ x: h.time, y: h.feels_like_avg })) },
              ]}
            />
          )}
        </ChartCard>

        <ChartCard title={t('heat.zones')} query={heat}>
          {(d) => {
            const zones = [...d.zones].sort((a, b) => a.district_id - b.district_id)
            return (
              <BarChart
                label="°C"
                labels={zones.map((z) => t('heat.zone', { n: z.district_id }))}
                values={zones.map((z) => z.heat.temperature_avg)}
                colors={zones.map((z) => LEVEL[z.heat.heat_level] ?? LEVEL.none)}
              />
            )
          }}
        </ChartCard>
      </div>

      <Card title={t('heat.cool')} bodyClassName="px-3 py-1 sm:px-4">
        {places.loading ? (
          <div className="py-3">
            <ListSkeleton rows={4} />
          </div>
        ) : places.error ? (
          <ErrorState error={places.error} onRetry={places.reload} />
        ) : (
          <ul className="divide-y divide-line">
            {cool.map((p, i) => (
              <li key={`cool-${i}`} className="flex items-center gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-ink">{name(p)}</p>
                  <p className="truncate text-sm text-muted">
                    {t(`kind.${p.kind}`)} · {formatDist(p.dist)}
                  </p>
                </div>
                <LocateButton
                  active={focus?.id === `cool-${i}`}
                  onClick={() => focusOn({ id: `cool-${i}`, lat: p.lat, lng: p.lng, label: name(p) })}
                />
              </li>
            ))}
          </ul>
        )}
      </Card>

      <ScrollHint />
    </div>
  )
}

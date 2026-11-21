import { useEffect, useMemo, useState } from 'react'
import MapPlaceholder from '../components/MapPlaceholder'
import LineBadge from '../components/transit/LineBadge'
import SaturdayReminder from '../components/transit/SaturdayReminder'
import { Card, ErrorState } from '../components/ui/Card'
import { CrosshairIcon } from '../components/ui/Icons'
import LocateButton from '../components/ui/LocateButton'
import { useUserLocation } from '../hooks/useUserLocation'
import ScrollHint from '../components/ui/ScrollHint'
import { ListSkeleton, Skeleton } from '../components/ui/Skeleton'
import { useApi } from '../hooks/useApi'
import { useAthensNow } from '../hooks/useAthensNow'
import { useMapFocus } from '../hooks/useMapFocus'
import { useLang } from '../i18n/LanguageContext'
import { api } from '../services/api'
import { distanceM, isRunning, lastToday, walkMinutes } from '../utils/transit'

const MODES = ['metro', 'tram', 'suburban']
const NEARBY_COUNT = 5
// Distances are measured from Syntagma Square until the user shares their location
const SYNTAGMA = { lat: 37.9755, lng: 23.7348 }
const pick = (obj, lang) => (typeof obj === 'string' ? obj : (obj?.[lang] ?? obj?.en))
const HALF_MIN = 30 * 1000

// Next departures at one station, per line and direction (official STASY timetable: an estimate, no live data)
function NextTrains({ station, lineById, name }) {
  const { t } = useLang()
  const deps = useApi(api.getDepartures, [station.id], { refreshMs: HALF_MIN })
  return (
    <Card title={`${t('transit.nextTrains')} · ${name}`} bodyClassName="px-3 py-2 sm:px-4">
      {deps.loading ? (
        <ListSkeleton rows={3} />
      ) : deps.error ? (
        <ErrorState error={deps.error} onRetry={deps.reload} />
      ) : (
        <>
          <ul className="divide-y divide-line">
            {deps.data.departures.map((d) => (
              <li key={`${d.line}|${d.towards}`} className="flex items-center gap-3 py-2.5">
                <LineBadge line={lineById[d.line]} />
                <span className="min-w-0 flex-1 truncate text-sm text-ink">{d.towards_en}</span>
                <span className="text-sm font-semibold tabular-nums text-ink">
                  {d.in_min.length
                    ? d.in_min.map((m) => (m === 0 ? t('transit.now') : t('transit.inMin', { n: m }))).join(' · ')
                    : t('transit.noMore')}
                </span>
              </li>
            ))}
          </ul>
          <p className="pt-2 text-xs text-muted">{t('transit.estimated')}</p>
        </>
      )}
    </Card>
  )
}

export default function Transit() {
  const { t, lang } = useLang()
  const now = useAthensNow()
  const lines = useApi(api.getTransitLines, [lang])
  const stations = useApi(api.getTransitStations, [lang])
  const { pos, status, locate } = useUserLocation()
  const { mapRef, focus, focusOn, clearFocus } = useMapFocus()
  const [mode, setMode] = useState('metro')
  const [stepFreeOnly, setStepFreeOnly] = useState(false)

  const origin = pos ?? SYNTAGMA
  const nearby = useMemo(
    () =>
      (stations.data ?? [])
        .filter((s) => !stepFreeOnly || s.stepFree)
        .map((s) => ({ ...s, dist: distanceM(origin, s) }))
        .sort((a, b) => a.dist - b.dist)
        .slice(0, NEARBY_COUNT),
    [stations.data, origin, stepFreeOnly],
  )
  const lineById = useMemo(() => Object.fromEntries((lines.data ?? []).map((l) => [l.id, l])), [lines.data])

  const formatDist = (m) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`)

  return (
    <div className="space-y-4">
      <SaturdayReminder variant="card" />

      {/* Map of the closest stations */}
      <MapPlaceholder
        ref={mapRef}
        center={origin}
        focus={focus}
        onClearFocus={clearFocus}
        loadingData={stations.loading}
        chips={nearby.map((s) => ({
          id: s.id,
          lat: s.lat,
          lng: s.lng,
          label: `${pick(s.name, lang)} · ${formatDist(s.dist)}`,
          color: lineById[s.lines[0]]?.color ?? '#94a3b8',
          badge: lineById[s.lines[0]]?.label,
        }))}
        overlay={
          <div>
            <p className="text-xs text-muted">{t('transit.nearby')}</p>
            <p className="text-sm font-semibold text-ink">{pos ? t('transit.fromYou') : t('transit.fromSyntagma')}</p>
          </div>
        }
      />

      <div className="grid gap-4 xl:grid-cols-5">
        {/* Closest stations */}
        <Card
          title={t('transit.nearby')}
          className="xl:col-span-2"
          bodyClassName="px-3 py-1 sm:px-4"
          action={
            <button
              onClick={locate}
              disabled={status === 'locating'}
              className="flex items-center gap-1.5 rounded-full bg-primary/15 px-3 py-1 text-xs font-semibold text-primary-dark transition hover:bg-primary hover:text-white disabled:opacity-60 dark:text-primary-light"
            >
              <CrosshairIcon className={`h-4 w-4 ${status === 'locating' ? 'animate-spin' : ''}`} />
              {status === 'locating' ? t('transit.locating') : t('transit.useLocation')}
            </button>
          }
        >
          {status === 'denied' && <p className="pt-2 text-xs text-muted">{t('transit.locationOff')}</p>}
          <button
            onClick={() => setStepFreeOnly((v) => !v)}
            aria-pressed={stepFreeOnly}
            className={`mt-2 rounded-full px-3 py-1 text-xs font-semibold transition ${
              stepFreeOnly ? 'bg-primary text-white' : 'bg-primary/10 text-primary-dark dark:text-primary-light'
            }`}
          >
            {t('transit.stepFreeOnly')}
          </button>
          {stations.loading ? (
            <div className="py-3">
              <ListSkeleton rows={4} />
            </div>
          ) : stations.error ? (
            <ErrorState error={stations.error} onRetry={stations.reload} />
          ) : (
            <ul className="divide-y divide-line">
              {nearby.map((s) => (
                <li key={s.id} className="flex items-center gap-3 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-ink">{pick(s.name, lang)}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-1">
                      {s.lines.map((id) => (
                        <LineBadge key={id} line={lineById[id]} />
                      ))}
                      <span className="ms-1 text-xs text-muted">
                        {formatDist(s.dist)} · {t('transit.walk', { m: walkMinutes(s.dist) })}
                      </span>
                      {s.stepFree && (
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-dark dark:text-primary-light">
                          {t('transit.stepFree')}
                        </span>
                      )}
                    </div>
                  </div>
                  <LocateButton
                    active={focus?.id === s.id}
                    onClick={() => focusOn({ id: s.id, lat: s.lat, lng: s.lng, label: pick(s.name, lang) })}
                  />
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Timetables */}
        <Card
          title={t('transit.timetables')}
          className="xl:col-span-3"
          bodyClassName="p-3 sm:p-4"
          action={
            <div role="tablist" className="flex rounded-full bg-primary/10 p-0.5 text-xs font-semibold">
              {MODES.map((m) => (
                <button
                  key={m}
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => setMode(m)}
                  className={`rounded-full px-2.5 py-1 transition sm:px-3 ${
                    mode === m ? 'bg-primary text-white shadow' : 'text-primary-dark hover:text-primary dark:text-primary-light'
                  }`}
                >
                  {t(`transit.${m}`)}
                </button>
              ))}
            </div>
          }
        >
          {lines.loading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-16 w-full rounded-lg" />
              ))}
            </div>
          ) : lines.error ? (
            <ErrorState error={lines.error} onRetry={lines.reload} />
          ) : (
            <ul className="space-y-2.5">
              {lines.data
                .filter((l) => l.mode === mode)
                .map((l) => {
                  const running = isRunning(l, now)
                  const last = lastToday(l, now)
                  const freq = l.freq && t('transit.every', { n: l.freq })
                  const nightFreq = l.satNightFreq && t('transit.nightEvery', { n: l.satNightFreq })
                  return (
                    <li key={l.id} className="rounded-lg bg-bg/60 p-3 ring-1 ring-line">
                      <div className="flex flex-wrap items-center gap-2">
                        <LineBadge line={l} size="lg" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold text-ink">
                            {l.mode === 'metro' ? t('transit.line', { n: l.label }) : l.label}
                            {l.airport && <span className="ms-1.5 font-normal text-muted">· ✈ {t('transit.airport')}</span>}
                          </p>
                          <p className="text-xs text-muted">{pick(l.route, lang)}</p>
                        </div>
                        <span
                          className={`flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold ${
                            running ? 'bg-green-500/15 text-green-700 dark:text-green-300' : 'bg-gray-500/15 text-muted'
                          }`}
                        >
                          <span className={`h-1.5 w-1.5 rounded-full ${running ? 'animate-pulse bg-green-500' : 'bg-gray-400'}`} />
                          {running ? t('transit.running') : t('transit.closed')}
                        </span>
                      </div>

                      <dl className="mt-2.5 grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-4">
                        <div>
                          <dt className="text-[11px] uppercase tracking-wide text-muted">{t('transit.first')}</dt>
                          <dd className="font-semibold tabular-nums text-ink">
                            {l.approx && '≈ '}
                            {l.first}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-[11px] uppercase tracking-wide text-muted">{t('transit.lastToday')}</dt>
                          <dd className={`font-semibold tabular-nums ${last === '24h' ? 'text-primary' : 'text-ink'}`}>
                            {last === '24h' ? t('transit.allNight') : `${l.approx ? '≈ ' : ''}${last}`}
                          </dd>
                        </div>
                        <div className="col-span-2 flex flex-wrap items-end gap-1.5 text-xs">
                          {freq && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">{freq}</span>}
                          {nightFreq && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-ink ring-1 ring-line">{nightFreq}</span>}
                          {l.allNightSat && (
                            <span className="rounded-full bg-primary/15 px-2 py-0.5 font-semibold text-primary-dark dark:text-primary-light">
                              {t('transit.sat24')}
                            </span>
                          )}
                        </div>
                      </dl>
                      {l.viaPikrodafni && <p className="mt-1.5 text-xs text-muted">{t('transit.viaPikrodafni')}</p>}
                    </li>
                  )
                })}
            </ul>
          )}
          {mode === 'suburban' && <p className="mt-3 text-xs text-muted">{t('transit.approx')}</p>}
          <p className="mt-3 text-[11px] leading-snug text-muted">{t('transit.source')}</p>
        </Card>
      </div>

      {nearby[0] && <NextTrains station={nearby[0]} lineById={lineById} name={pick(nearby[0].name, lang)} />}

      <ScrollHint />
    </div>
  )
}

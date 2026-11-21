import MapPlaceholder from '../components/MapPlaceholder'
import { Card, ErrorState } from '../components/ui/Card'
import { useMemo, useState } from 'react'
import { EventsIcon, FlameIcon } from '../components/ui/Icons'
import LocateButton from '../components/ui/LocateButton'
import ScrollHint from '../components/ui/ScrollHint'
import { ListSkeleton } from '../components/ui/Skeleton'
import { useApi } from '../hooks/useApi'
import { useMapFocus } from '../hooks/useMapFocus'
import { useLang } from '../i18n/LanguageContext'
import { api } from '../services/api'

export default function Events() {
  const { t, lang, locale } = useLang()
  const events = useApi(api.getEvents, [lang])
  const { mapRef, focus, focusOn, clearFocus } = useMapFocus()
  const [sort, setSort] = useState('date') // 'date' | 'popular'

  const list = useMemo(() => {
    const rows = [...(events.data ?? [])]
    return sort === 'popular'
      ? rows.sort((a, b) => (b.popularity ?? -1) - (a.popularity ?? -1))
      : rows.sort((a, b) => a.date.localeCompare(b.date))
  }, [events.data, sort])

  const compact = (n) => new Intl.NumberFormat(locale, { notation: 'compact', maximumFractionDigits: 1 }).format(n)

  const price = (e) =>
    e.pricePerPerson > 0
      ? new Intl.NumberFormat(locale, { style: 'currency', currency: e.currency || 'EUR', maximumFractionDigits: 0 }).format(e.pricePerPerson)
      : null

  return (
    <div className="space-y-4">
      <MapPlaceholder ref={mapRef} focus={focus} onClearFocus={clearFocus} />

      <h1 className="text-lg font-semibold text-ink">{t('events.title')}</h1>

      <Card
        title={t('events.upcoming')}
        bodyClassName="px-3 py-1 sm:px-4"
        action={
          // sorting by popularity only when the data has it (the real events feed does not)
          (events.data ?? []).some((e) => e.popularity != null) && <div role="group" aria-label={t('events.sortBy')} className="flex rounded-full bg-primary/10 p-0.5 text-xs font-semibold">
            {[
              ['date', t('events.sortDate')],
              ['popular', t('events.sortPopular')],
            ].map(([id, label]) => (
              <button
                key={id}
                onClick={() => setSort(id)}
                aria-pressed={sort === id}
                className={`rounded-full px-2.5 py-1 transition sm:px-3 ${
                  sort === id ? 'bg-primary text-white shadow' : 'text-primary-dark hover:text-primary dark:text-primary-light'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        }
      >
        {events.loading ? (
          <div className="py-3">
            <ListSkeleton rows={4} />
          </div>
        ) : events.error ? (
          <ErrorState error={events.error} onRetry={events.reload} />
        ) : (
          <ul className="divide-y divide-line">
            {list.map((e) => {
              const p = price(e)
              return (
                <li key={e.id} className="flex items-center gap-3 py-3">
                  {/* date badge */}
                  <div className="flex w-12 shrink-0 flex-col items-center rounded-lg bg-primary/10 py-1.5 text-primary-dark dark:text-primary-light">
                    <span className="text-[11px] font-medium uppercase leading-none">
                      {new Date(e.date).toLocaleDateString(locale, { month: 'short' })}
                    </span>
                    <span className="text-lg font-bold leading-tight">{new Date(e.date).getDate()}</span>
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="font-medium leading-snug text-ink">{e.title}</p>
                    <p className="truncate text-sm text-muted">
                      {e.venue === e.area ? e.venue : `${e.venue} · ${e.area}`}
                    </p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-dark dark:text-primary-light">
                        <EventsIcon className="h-3 w-3" />
                        {e.type}
                      </span>
                      {/* average price per person (unknown → not shown: never claim "free" without data) */}
                      {e.pricePerPerson != null && <span
                        title={t('events.avgPrice')}
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                          p ? 'bg-surface-2 text-ink ring-1 ring-line' : 'bg-green-500/15 text-green-700 dark:text-green-300'
                        }`}
                      >
                        {p ? (
                          <>
                            <span className="sr-only">{t('events.avgPrice')}: </span>~{p} <span className="font-normal text-muted">{t('events.perPerson')}</span>
                          </>
                        ) : (
                          t('events.free')
                        )}
                      </span>}
                    </div>

                    {/* popularity rate (only when the backend has it) */}
                    {e.popularity != null && (<div className="mt-2 flex max-w-xs items-center gap-2" title={`${t('events.popularity')}: ${e.popularity}%`}>
                      <FlameIcon className={`h-4 w-4 shrink-0 ${e.popularity >= 80 ? 'text-orange-500' : 'text-primary'}`} />
                      <div
                        className="h-1.5 flex-1 overflow-hidden rounded-full bg-skel"
                        role="meter"
                        aria-label={t('events.popularity')}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={e.popularity}
                      >
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-primary to-orange-500"
                          style={{ width: `${e.popularity}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold tabular-nums text-ink">{e.popularity}%</span>
                      {e.interested != null && <span className="hidden text-xs text-muted sm:inline">· {t('events.interested', { n: compact(e.interested) })}</span>}
                    </div>)}
                  </div>

                  {/* location point button */}
                  <LocateButton
                    active={focus?.id === e.id}
                    onClick={() => focusOn({ id: e.id, lat: e.lat, lng: e.lng, label: `${e.title} · ${e.venue}` })}
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

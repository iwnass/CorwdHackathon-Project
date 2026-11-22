import { useMemo, useState } from 'react'
import MapPlaceholder from '../components/MapPlaceholder'
import { Card, ErrorState } from '../components/ui/Card'
import LocateButton from '../components/ui/LocateButton'
import ScrollHint from '../components/ui/ScrollHint'
import { ListSkeleton } from '../components/ui/Skeleton'
import { useApi } from '../hooks/useApi'
import { useMapFocus } from '../hooks/useMapFocus'
import { useUserLocation } from '../hooks/useUserLocation'
import { useLang } from '../i18n/LanguageContext'
import { api } from '../services/api'
import { distanceM } from '../utils/transit'

const SYNTAGMA = { lat: 37.9755, lng: 23.7348 }
// What visitors look for first; the 302 named squares/places are a filter of their own
const KINDS = ['museum', 'gallery', 'theatre', 'cultural_centre', 'library', 'cinema', 'place', 'free_wifi', 'accessible_parking']
const COLOR = { museum: '#8b5cf6', gallery: '#ec4899', theatre: '#ef4444', cultural_centre: '#f59e0b', library: '#0ea5e9', cinema: '#6366f1', place: '#64748b', free_wifi: '#14b8a6', accessible_parking: '#2563eb' }
const SHOWN = 40

export default function Places() {
  const { t, lang } = useLang()
  const places = useApi(api.getPlaces, [])
  const { pos } = useUserLocation()
  const { mapRef, focus, focusOn, clearFocus } = useMapFocus()
  const [kind, setKind] = useState('museum')

  const origin = pos ?? SYNTAGMA
  const name = (p) => (lang === 'el' ? p.name : p.name_en || p.name)
  const list = useMemo(
    () =>
      (places.data ?? [])
        .filter((p) => p.kind === kind)
        .map((p) => ({ ...p, dist: distanceM(origin, p) }))
        .sort((a, b) => a.dist - b.dist),
    [places.data, kind, origin],
  )
  const formatDist = (m) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`)

  return (
    <div className="space-y-4">
      <MapPlaceholder
        ref={mapRef}
        focus={focus}
        onClearFocus={clearFocus}
        loadingData={places.loading}
        chips={list.slice(0, 12).map((p, i) => ({ id: `${p.kind}-${i}`, lat: p.lat, lng: p.lng, label: name(p), color: COLOR[p.kind] }))}
        overlay={
          <div>
            <p className="text-xs text-muted">{t('places.title')}</p>
            <p className="text-sm font-semibold text-ink">
              {list.length} · {t(`kind.${kind}`)}
            </p>
          </div>
        }
      />

      <h1 className="font-display text-xl font-bold tracking-tight sm:text-2xl bg-gradient-to-r from-primary-darker via-violet-600 to-fuchsia-500 bg-clip-text text-transparent dark:from-primary-light dark:via-violet-400 dark:to-fuchsia-400">{t('places.title')}</h1>

      <div role="group" aria-label={t('places.filter')} className="flex flex-wrap gap-2">
        {KINDS.map((k) => (
          <button
            key={k}
            onClick={() => setKind(k)}
            aria-pressed={kind === k}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              kind === k ? 'bg-primary text-white shadow' : 'bg-primary/10 text-primary-dark hover:bg-primary/20 dark:text-primary-light'
            }`}
          >
            {t(`kind.${k}`)}
          </button>
        ))}
      </div>

      <Card title={t(`kind.${kind}`)} bodyClassName="px-3 py-1 sm:px-4">
        {places.loading ? (
          <div className="py-3">
            <ListSkeleton rows={4} />
          </div>
        ) : places.error ? (
          <ErrorState error={places.error} onRetry={places.reload} />
        ) : (
          <ul className="divide-y divide-line">
            {list.slice(0, SHOWN).map((p, i) => (
              <li key={`${p.kind}-${i}`} className="flex items-center gap-3 py-3">
                <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: COLOR[p.kind] }} />
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-ink">
                    {p.link ? (
                      <a href={p.link} target="_blank" rel="noopener noreferrer" className="hover:underline">
                        {name(p)}
                      </a>
                    ) : (
                      name(p)
                    )}
                  </p>
                  <p className="truncate text-sm text-muted">{[p.address, formatDist(p.dist)].filter(Boolean).join(' · ')}</p>
                </div>
                <LocateButton
                  active={focus?.id === `${p.kind}-${i}`}
                  onClick={() => focusOn({ id: `${p.kind}-${i}`, lat: p.lat, lng: p.lng, label: name(p) })}
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

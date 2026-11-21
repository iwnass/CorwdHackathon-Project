import { forwardRef, useEffect, useState } from 'react'
import { CircleLoader } from 'react-spinners'
import { config } from '../config'
import { useLang } from '../i18n/LanguageContext'
import { CloseIcon, ExternalIcon, MapPinIcon } from './ui/Icons'

/**
 * Google Map placeholder (keyless embed, in the user's language).
 *
 * props
 *   chips:   [{ id, label, color }]  small labels at the bottom (stations, chargers…)
 *   overlay: small card top-left (any content)
 *   center:  { lat, lng } to centre the map on (default: Athens centre)
 *   focus:   { lat, lng, label } → map zooms there + "Open in Google Maps" link
 *   onClearFocus: called by the "Show all Athens" button
 *
 * To switch to a real interactive map, install `@vis.gl/react-google-maps`,
 * set VITE_GOOGLE_MAPS_API_KEY and replace the <iframe>; the props stay the same.
 */
const MapPlaceholder = forwardRef(function MapPlaceholder(
  { chips = [], overlay, center, loadingData = false, focus, onClearFocus, height = 'h-56 sm:h-64 lg:h-[clamp(220px,36vh,380px)]' },
  ref,
) {
  const { t, mapsLang } = useLang()
  const [mapLoaded, setMapLoaded] = useState(false)
  const [minTimeDone, setMinTimeDone] = useState(false)

  const target = focus ?? center ?? config.athensCenter
  const zoom = focus ? 17 : center ? 15 : 13
  const src = `https://maps.google.com/maps?q=${target.lat},${target.lng}&z=${zoom}&hl=${mapsLang}&output=embed`

  // Show the loader each time the map changes (first load, language, focus)
  useEffect(() => {
    setMapLoaded(false)
    setMinTimeDone(false)
    const id = setTimeout(() => setMinTimeDone(true), focus ? 500 : 900)
    return () => clearTimeout(id)
  }, [src, focus])

  const showLoader = !mapLoaded || !minTimeDone
  const googleLink = `https://www.google.com/maps/search/?api=1&query=${target.lat},${target.lng}`

  return (
    <div ref={ref} className={`relative scroll-mt-4 overflow-hidden rounded-xl bg-surface-2 ring-1 ring-line ${height}`}>
      <iframe
        key={src}
        title={t('map.title')}
        src={src}
        className={`h-full w-full border-0 transition-opacity duration-500 dark:brightness-90 ${showLoader ? 'opacity-0' : 'opacity-100'}`}
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        onLoad={() => setMapLoaded(true)}
      />

      {showLoader && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-surface-2">
          <CircleLoader color="#00cd9a" size={53} speedMultiplier={0.55} />
          <p className="text-sm text-muted">{t('map.loading')}</p>
        </div>
      )}

      {!showLoader && focus && (
        <div className="absolute inset-x-3 top-3 flex flex-wrap items-center gap-2">
          <span className="flex min-w-0 items-center gap-1.5 rounded-lg bg-surface/95 px-3 py-2 text-sm font-medium text-ink shadow-md ring-1 ring-line backdrop-blur">
            <MapPinIcon className="h-4 w-4 shrink-0 text-primary" />
            <span className="truncate">{focus.label}</span>
          </span>
          <a
            href={googleLink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white shadow-md hover:bg-primary-dark"
          >
            <ExternalIcon className="h-4 w-4" />
            <span className="hidden sm:inline">{t('map.openGoogle')}</span>
            <span className="sm:hidden">Google Maps</span>
          </a>
          {onClearFocus && (
            <button
              onClick={onClearFocus}
              className="ms-auto flex items-center gap-1 rounded-lg bg-surface/95 px-2.5 py-2 text-sm text-muted shadow-md ring-1 ring-line backdrop-blur hover:text-ink"
            >
              <CloseIcon className="h-4 w-4" />
              <span className="hidden sm:inline">{t('map.reset')}</span>
            </button>
          )}
        </div>
      )}

      {!showLoader && !focus && (overlay || loadingData) && (
        <div className="absolute start-3 top-3 max-w-[75%] rounded-lg bg-surface/90 p-2.5 shadow-md ring-1 ring-line backdrop-blur sm:p-3">
          {loadingData ? (
            <div className="w-36 animate-pulse space-y-2">
              <div className="h-3 w-24 rounded bg-skel" />
              <div className="h-6 w-16 rounded bg-skel" />
            </div>
          ) : (
            overlay
          )}
        </div>
      )}

      {!showLoader && !focus && chips.length > 0 && (
        // one scrollable row on phones, wraps on bigger screens
        <div className="absolute inset-x-3 bottom-3 flex gap-2 overflow-x-auto pb-0.5 [scrollbar-width:none] sm:flex-wrap">
          {chips.map((c) => (
            <span
              key={c.id}
              title={c.title}
              className="flex shrink-0 items-center gap-1.5 rounded-full bg-surface/90 px-2.5 py-1 text-xs font-medium text-ink shadow ring-1 ring-line backdrop-blur"
            >
              <span className="h-2 w-2 rounded-full" style={{ background: c.color }} />
              {c.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
})

export default MapPlaceholder


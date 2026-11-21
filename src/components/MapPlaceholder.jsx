import { Language, MapStyle, Map as MtMap, Marker, config as mtConfig } from '@maptiler/sdk'
import '@maptiler/sdk/dist/maptiler-sdk.css'
import { forwardRef, useEffect, useRef, useState } from 'react'
import { CircleLoader } from 'react-spinners'
import { config } from '../config'
import { useTheme } from '../context/ThemeContext'
import { useUserLocation } from '../hooks/useUserLocation'
import { useLang } from '../i18n/LanguageContext'
import { CloseIcon, CrosshairIcon, ExternalIcon, MapPinIcon } from './ui/Icons'

const MT_LANG = { zh: Language.TRADITIONAL_CHINESE } // the app's other codes are MapTiler codes as they are
const style = (dark) => (dark ? MapStyle.STREETS.DARK : MapStyle.STREETS)

// The base style's own station icons/labels duplicate our chips/badges: hide them, keep the rail/road lines
const BASE_TRANSIT_LAYER_RE = /rail|subway|metro|tram|station|transit/i
function hideBaseTransitLayers(map) {
  for (const layer of map.getStyle()?.layers ?? []) {
    if (layer.type !== 'symbol') continue
    const probe = `${layer.id} ${layer['source-layer'] ?? ''} ${JSON.stringify(layer.filter ?? '')}`
    if (BASE_TRANSIT_LAYER_RE.test(probe)) {
      try { map.setLayoutProperty(layer.id, 'visibility', 'none') } catch { /* layer not ready yet */ }
    }
  }
}

// A transit station: a line-coloured round badge (matches <LineBadge>) instead of a plain pin
function badgeElement(p) {
  const el = document.createElement('div')
  el.className = 'map-badge'
  el.style.background = p.color
  el.textContent = p.badge
  return el
}

/** Interactive MapTiler map: flies to `target`, draws a marker for every chip with lat/lng and for `focus`. */
function TileMap({ target, zoom, chips, focus, user, userLabel, onLoad }) {
  const { lang } = useLang()
  const { isDark } = useTheme()
  const box = useRef(null)
  const map = useRef(null)
  const markers = useRef([])
  const userMarker = useRef(null)

  useEffect(() => {
    mtConfig.apiKey = config.maptilerKey
    map.current = new MtMap({
      container: box.current, style: style(isDark), center: [target.lng, target.lat], zoom,
      language: MT_LANG[lang] ?? lang, navigationControl: 'bottom-right', geolocateControl: false,
    })
    map.current.once('load', onLoad)
    map.current.on('styledata', () => hideBaseTransitLayers(map.current)) // style reloads on theme/language change too
    return () => map.current.remove()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps -- created once; the effects below keep it in sync

  useEffect(() => { map.current.setStyle(style(isDark)) }, [isDark])
  useEffect(() => { map.current.setLanguage(MT_LANG[lang] ?? lang) }, [lang])
  useEffect(() => { map.current.flyTo({ center: [target.lng, target.lat], zoom }) }, [target.lat, target.lng, zoom])
  // a new position from "Use my location": go there (unless the user is looking at a chosen place)
  useEffect(() => { if (user && !focus) map.current.flyTo({ center: [user.lng, user.lat], zoom: 15 }) }, [user?.lat, user?.lng]) // eslint-disable-line react-hooks/exhaustive-deps

  // chips change identity on every parent render: rebuild the markers only when what they show changes
  const points = [
    ...chips.filter((c) => c.lat != null),
    ...(focus ? [{ ...focus, color: '#e11d48' }] : []),
  ]
  const pointsKey = points.map((p) => `${p.id}|${p.lat}|${p.lng}|${p.color}|${p.badge ?? ''}`).join()
  useEffect(() => {
    markers.current.forEach((m) => m.remove())
    markers.current = points.map((p) => {
      const m = p.badge
        ? new Marker({ element: badgeElement(p) }).setLngLat([p.lng, p.lat]).addTo(map.current)
        : new Marker({ color: p.color }).setLngLat([p.lng, p.lat]).addTo(map.current)
      m.getElement().title = p.label ?? ''
      return m
    })
  }, [pointsKey]) // eslint-disable-line react-hooks/exhaustive-deps

  // "you are here": an Apple Find My-style pulsing dot instead of a pin
  useEffect(() => {
    if (!user) {
      userMarker.current?.remove()
      userMarker.current = null
      return
    }
    if (!userMarker.current) {
      const el = document.createElement('div')
      el.className = 'locate-dot'
      el.innerHTML = '<span class="locate-dot__pulse"></span><span class="locate-dot__core"></span>'
      el.title = userLabel ?? ''
      userMarker.current = new Marker({ element: el, anchor: 'center' }).setLngLat([user.lng, user.lat]).addTo(map.current)
    } else {
      userMarker.current.setLngLat([user.lng, user.lat])
    }
  }, [user?.lat, user?.lng, userLabel]) // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={box} className="h-full w-full" />
}

/**
 * The page map: MapTiler (interactive, markers). Needs VITE_MAPTILER_KEY.
 *
 * props
 *   chips:   [{ id, label, color, lat?, lng? }]  small labels at the bottom; with lat/lng also a marker on the map
 *   overlay: small card top-left (any content)
 *   center:  { lat, lng } to centre the map on (default: Athens centre)
 *   focus:   { lat, lng, label } → map flies there + "Open in Google Maps" link (directions in the visitor's app)
 *   onClearFocus: called by the "Show all Athens" button
 */
const MapPlaceholder = forwardRef(function MapPlaceholder(
  { chips = [], overlay, center, loadingData = false, focus, onClearFocus, height = 'h-56 sm:h-64 lg:h-[clamp(220px,36vh,380px)]' },
  ref,
) {
  const { t } = useLang()
  const { pos, status, locate } = useUserLocation()
  const [mapLoaded, setMapLoaded] = useState(false)

  const target = focus ?? center ?? config.athensCenter
  const zoom = focus ? 17 : center ? 15 : 13
  const tiles = Boolean(config.maptilerKey)
  const showLoader = tiles && !mapLoaded
  const googleLink = `https://www.google.com/maps/search/?api=1&query=${target.lat},${target.lng}`

  return (
    <div ref={ref} className={`relative scroll-mt-4 overflow-hidden rounded-xl bg-surface-2 ring-1 ring-line ${height}`}>
      {tiles ? (
        <div className={`h-full w-full transition-opacity duration-500 ${showLoader ? 'opacity-0' : 'opacity-100'}`}>
          <TileMap target={target} zoom={zoom} chips={chips} focus={focus} user={pos} userLabel={t('transit.fromYou')} onLoad={() => setMapLoaded(true)} />
        </div>
      ) : (
        <p className="flex h-full items-center justify-center p-6 text-center text-sm text-muted">
          Map unavailable: set VITE_MAPTILER_KEY in .env.local (free key at maptiler.com) and restart the app.
        </p>
      )}

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

      {tiles && !showLoader && !focus && (
        <button
          onClick={locate}
          disabled={status === 'locating'}
          className="absolute end-3 top-3 z-10 flex items-center gap-1.5 rounded-full bg-primary px-3 py-2 text-xs font-semibold text-white shadow-md transition hover:bg-primary-dark disabled:opacity-60"
        >
          <CrosshairIcon className={`h-4 w-4 ${status === 'locating' ? 'animate-spin' : ''}`} />
          {status === 'locating' ? t('transit.locating') : t('transit.useLocation')}
        </button>
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


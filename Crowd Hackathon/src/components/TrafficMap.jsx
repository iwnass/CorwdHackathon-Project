import { useState } from 'react'
import { MapContainer, Polyline, Rectangle, TileLayer, CircleMarker, Tooltip } from 'react-leaflet'
import { ATHENS_BOUNDS, ATHENS_CENTER, TOMTOM_KEY } from '../config'
import { getAqiCategory } from '../lib/aqi'
import { congestionLevel } from '../lib/traffic'
import { Card, CardHeader } from './ui/Card'

const TILES = {
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
}
const TOMTOM_FLOW = `https://api.tomtom.com/traffic/map/4/tile/flow/relative0/{z}/{x}/{y}.png?key=${TOMTOM_KEY}`

function Chip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-xs font-medium shadow transition ${
        active ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50 dark:bg-ink-800 dark:text-gray-300'
      }`}
    >
      {children}
    </button>
  )
}

export function TrafficMap({ corridors, districts, dark }) {
  const [showTraffic, setShowTraffic] = useState(true)
  const [showAir, setShowAir] = useState(true)
  const hasLiveTraffic = Boolean(TOMTOM_KEY)

  return (
    <Card id="map" className="overflow-hidden">
      <CardHeader
        title="Live map"
        subtitle={hasLiveTraffic ? 'Live traffic by TomTom · air quality by Open-Meteo' : 'Demo traffic estimate · air quality by Open-Meteo'}
      />
      <div className="relative mt-4 h-[460px] border-t border-gray-100 dark:border-white/5">
        <div className="absolute right-3 top-3 z-[1000] flex gap-2">
          <Chip active={showTraffic} onClick={() => setShowTraffic((v) => !v)}>Traffic</Chip>
          <Chip active={showAir} onClick={() => setShowAir((v) => !v)}>Air quality</Chip>
        </div>

        <MapContainer
          center={ATHENS_CENTER}
          zoom={13}
          minZoom={12}
          maxZoom={17}
          maxBounds={ATHENS_BOUNDS}
          maxBoundsViscosity={1}
          className="h-full w-full"
        >
          <TileLayer
            key={dark ? 'dark' : 'light'}
            url={dark ? TILES.dark : TILES.light}
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />

          <Rectangle bounds={ATHENS_BOUNDS} pathOptions={{ color: '#8b5cf6', weight: 1.5, dashArray: '6 6', fill: false }} />

          {showTraffic && hasLiveTraffic && <TileLayer url={TOMTOM_FLOW} opacity={0.9} attribution="Traffic &copy; TomTom" />}

          {showTraffic && !hasLiveTraffic &&
            corridors.map((c) => (
              <Polyline key={c.id} positions={c.path} pathOptions={{ color: congestionLevel(c.value).hex, weight: 7, opacity: 0.85, lineCap: 'round' }}>
                <Tooltip sticky>
                  <strong>{c.name}</strong>
                  <br />
                  {congestionLevel(c.value).label} · {c.value}%
                </Tooltip>
              </Polyline>
            ))}

          {showAir &&
            districts.map((d) => {
              const cat = getAqiCategory(d.aqi)
              return (
                <CircleMarker
                  key={d.id}
                  center={[d.lat, d.lon]}
                  radius={16}
                  pathOptions={{ color: '#fff', weight: 2, fillColor: cat.hex, fillOpacity: 0.85 }}
                >
                  <Tooltip direction="top" offset={[0, -10]} permanent={false}>
                    <strong>{d.name}</strong>
                    <br />
                    AQI {d.aqi} · {cat.short}
                  </Tooltip>
                </CircleMarker>
              )
            })}
        </MapContainer>
      </div>
    </Card>
  )
}

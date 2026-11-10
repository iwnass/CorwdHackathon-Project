import { useCallback, useEffect, useState } from 'react'
import { DISTRICTS, REFRESH_MS } from '../config'

// Open-Meteo Air Quality API – free, no key. https://open-meteo.com/en/docs/air-quality-api
const URL_BASE = 'https://air-quality-api.open-meteo.com/v1/air-quality'

function buildUrl() {
  const params = new URLSearchParams({
    latitude: DISTRICTS.map((d) => d.lat).join(','),
    longitude: DISTRICTS.map((d) => d.lon).join(','),
    current: 'us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone',
    hourly: 'us_aqi',
    past_days: '1',
    forecast_days: '1',
    timezone: 'Europe/Athens',
  })
  return `${URL_BASE}?${params}`
}

function parse(json) {
  const list = Array.isArray(json) ? json : [json]
  const districts = DISTRICTS.map((d, i) => {
    const c = list[i]?.current ?? {}
    return {
      ...d,
      aqi: Math.round(c.us_aqi ?? 0),
      pm25: c.pm2_5 ?? 0,
      pm10: c.pm10 ?? 0,
      no2: c.nitrogen_dioxide ?? 0,
      o3: c.ozone ?? 0,
    }
  })

  // City-average hourly series: last 24 h + next 6 h
  const times = list[0]?.hourly?.time ?? []
  const nowIdx = Math.max(0, times.indexOf(list[0]?.current?.time?.slice(0, 13) + ':00'))
  const from = Math.max(0, nowIdx - 23)
  const to = Math.min(times.length, nowIdx + 7)
  const hourly = []
  for (let i = from; i < to; i++) {
    const vals = list.map((l) => l.hourly?.us_aqi?.[i]).filter((v) => typeof v === 'number')
    if (vals.length) hourly.push({ time: times[i], aqi: Math.round(vals.reduce((a, b) => a + b, 0) / vals.length), isNow: i === nowIdx })
  }
  return { districts, hourly }
}

// Fallback so the UI still works offline / if the API is down (clearly flagged as demo)
function demoData() {
  const now = new Date()
  const districts = DISTRICTS.map((d, i) => {
    const aqi = 62 + ((i * 17) % 38)
    return { ...d, aqi, pm25: aqi / 3.2, pm10: aqi / 2, no2: 20 + i * 3, o3: 45 + i * 4 }
  })
  const hourly = Array.from({ length: 30 }, (_, i) => {
    const h = new Date(now.getTime() + (i - 23) * 3600e3)
    return { time: h.toISOString(), aqi: Math.round(70 + 22 * Math.sin(i / 4) + (i % 3) * 3), isNow: i === 23 }
  })
  return { districts, hourly }
}

export function useAirQuality() {
  const [state, setState] = useState({ districts: [], hourly: [], loading: true, error: null, isDemo: false, updatedAt: null })

  const load = useCallback(async () => {
    try {
      const res = await fetch(buildUrl())
      if (!res.ok) throw new Error(`Air quality API returned ${res.status}`)
      const data = parse(await res.json())
      setState({ ...data, loading: false, error: null, isDemo: false, updatedAt: new Date() })
    } catch (err) {
      setState({ ...demoData(), loading: false, error: err.message, isDemo: true, updatedAt: new Date() })
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [load])

  return { ...state, refresh: load }
}

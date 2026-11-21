import { useEffect, useSyncExternalStore } from 'react'

// Browser location, shared by every page and map: asked only when the user taps "Use my location"
// (or straight away if the browser already allows it). One position for the whole app.
let state = { pos: null, status: 'idle' } // status: idle | locating | ok | denied
const listeners = new Set()
const set = (next) => {
  state = next
  listeners.forEach((f) => f())
}

export function locate() {
  if (!navigator.geolocation) return set({ pos: null, status: 'denied' })
  set({ ...state, status: 'locating' })
  navigator.geolocation.getCurrentPosition(
    (p) => set({ pos: { lat: p.coords.latitude, lng: p.coords.longitude }, status: 'ok' }),
    () => set({ pos: null, status: 'denied' }),
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
  )
}

let checked = false
export function useUserLocation() {
  const s = useSyncExternalStore((f) => (listeners.add(f), () => listeners.delete(f)), () => state)
  useEffect(() => {
    if (checked) return
    checked = true
    navigator.permissions
      ?.query({ name: 'geolocation' })
      .then((r) => r.state === 'granted' && locate())
      .catch(() => {})
  }, [])
  return { ...s, locate }
}

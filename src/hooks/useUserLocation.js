import { useEffect, useSyncExternalStore } from 'react'

// Browser location, shared by every page and map: asked only when the user taps "Use my location"
// (or straight away if the browser already allows it). One position for the whole app.
let state = { pos: null, status: 'idle' } // status: idle | locating | ok | denied
const listeners = new Set()
const set = (next) => {
  state = next
  listeners.forEach((f) => f())
}

export const currentPosition = () => state.pos // for non-React code (e.g. the chat request)

export function locate() {
  if (!navigator.geolocation) return set({ pos: null, status: 'denied' })
  set({ ...state, status: 'locating' })
  navigator.geolocation.getCurrentPosition(
    (p) => set({ pos: { lat: p.coords.latitude, lng: p.coords.longitude }, status: 'ok' }),
    () => set({ pos: null, status: 'denied' }),
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
  )
}

export function useUserLocation() {
  const s = useSyncExternalStore((f) => (listeners.add(f), () => listeners.delete(f)), () => state)
  useEffect(() => {
    // Re-checked on every page's map mount (not just once per app load): if the first
    // attempt never got a position (permission still pending, a slow/failed GPS fix…),
    // switching tabs should pick it up as soon as it's granted, without needing a refresh.
    if (state.status !== 'idle') return
    navigator.permissions
      ?.query({ name: 'geolocation' })
      .then((r) => r.state === 'granted' && locate())
      .catch(() => {})
  }, [])
  return { ...s, locate }
}

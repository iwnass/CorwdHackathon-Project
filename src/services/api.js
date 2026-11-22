/**
 * THE ONLY FILE THE BACKEND TEAM NEEDS TO TOUCH.
 *
 * Every function returns a Promise with the data shape documented in
 * mockData.js. With VITE_USE_MOCKS=true the mocks are used; set it to false
 * and the same functions call the real endpoints below.
 *
 * `lang` is 'en' or 'el' and is sent as ?lang=… so the backend can return
 * place names / event titles / agent replies in the user's language.
 * If an endpoint path or response shape differs, adapt it here — the
 * components won't need to change.
 */
import { config } from '../config'
import { http } from './http'
import { mock } from './mockData'
import { TRANSIT_LINES } from './transitData'
import { currentPosition } from '../hooks/useUserLocation'

// Adapters: the backend's endpoints → the shapes in mockData.js. Fields the backend has no data for are null
// (the pages hide them) — never invented.
const AROUND_ATHENS_M = 6000 // EV map: the municipality and its edge, not all ~1000 chargers of Attica
const distM = (a, b) => {
  const r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2
  return 2 * 6371008.8 * Math.asin(Math.min(1, Math.sqrt(h)))
}
let conversationId = null // the city assistant keeps the dialogue on its side

const real = {
  // GET /api/events (Ticketmaster): one entry per show (its next performance)
  getEvents: async () => {
    const r = await http('/events', { params: { days: 60, limit: 200 } })
    const seen = new Set()
    return r.events
      .filter((e) => !seen.has(`${e.name}|${e.venue.name}`) && seen.add(`${e.name}|${e.venue.name}`))
      .map((e) => ({
        id: e.id,
        date: e.date,
        title: e.name,
        venue: e.venue.name,
        area: e.venue.neighbourhood || e.venue.city || e.venue.name,
        lat: e.venue.lat,
        lng: e.venue.lon,
        type: e.category || e.genre || '',
        category: e.category || null,
        pricePerPerson: e.price?.min ?? null,
        currency: e.price?.currency || 'EUR',
        popularity: null,
        interested: null,
        url: e.url,
        status: e.status,
      }))
  },

  // GET /api/metro: real station coordinates and lines. Line timetables stay the curated list in transitData.js
  // (newer than the official STASY file, which only covers summer 2026).
  getTransitLines: async () => TRANSIT_LINES,
  getTransitStations: async () => {
    const r = await http('/metro')
    return r.stations.map((s) => ({
      id: s.id, name: { en: s.name_en, el: s.name }, lat: s.lat, lng: s.lon, lines: s.lines, stepFree: s.step_free,
    }))
  },

  // GET /api/ev (national registry, live availability every 10 min)
  getEvStations: async () => {
    const r = await http('/ev')
    return r.chargers
      .filter((c) => distM(config.athensCenter, { lat: c.lat, lng: c.lon }) <= AROUND_ATHENS_M)
      .map((c) => {
        const out = (c.status.ev_out_of_order || 0) + (c.status.ev_unknown || 0)
        return {
          id: c.id, name: c.name, address: c.address, lat: c.lat, lng: c.lon,
          powerKw: c.max_kw, connectors: c.plugs, total: c.points, available: c.available,
          pricePerKwh: null, // not published by the registry
          status: c.available > 0 ? 'available' : out >= c.points ? 'offline' : 'busy',
        }
      })
  },

  // GET /api/ev?history=1: our own 10-minute samples of live availability (the registry keeps no history)
  getEvUsage: async () => (await http('/ev', { params: { history: 1 } })).history.map((r) => ({ time: r.time * 1000, occupancy: r.occupancy })),

  // GET /api/metro?station=: next departures per line and direction (timetable estimates)
  getDepartures: (stationId) => http('/metro', { params: { station: stationId } }),

  // GET /api/places: museums, theatres, sights, free WiFi, accessible parking, fountains, pools… (city GIS)
  getPlaces: async () => (await http('/places')).places.map((p) => ({ ...p, lng: p.lon })),

  // GET /api/heat + /api/zones: today's hourly temperature for the city and each zone (municipal district)
  getHeat: async () => {
    const [heat, zones] = await Promise.all([http('/heat'), http('/zones')])
    return { city: heat.city, hourly: heat.hourly, zones: zones.zones.filter((z) => z.heat) }
  },

  // GET /api/parking: parking stations near the centre (OpenStreetMap): garages and named public lots
  getParking: async () => (await http('/parking')).parking.map((p) => ({ ...p, lng: p.lon })),

  // POST /api/assistant: the City of Athens assistant (+ heat/cool-down answers from our data, near the user)
  askAgent: async (message) => {
    const pos = currentPosition()
    const r = await http('/assistant', {
      method: 'POST',
      body: { text: message, conversation_id: conversationId, ...(pos && { lat: pos.lat, lon: pos.lng }) },
    })
    conversationId = r.conversation_id
    return { reply: r.text }
  },
}

export const api = config.useMocks ? mock : real

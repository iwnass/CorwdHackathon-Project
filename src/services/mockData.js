import { translations } from '../i18n/translations'
import { TRANSIT_LINES, TRANSIT_STATIONS } from './transitData'

// Fake responses with EXACTLY the shape the frontend expects from the backend.
// The backend team can use this file as the API contract (see also README.md).
// `lang` is one of the codes in src/i18n/translations.js. Demo place names and event
// titles exist in English and Greek; other languages fall back to English (the real
// backend should return them in the requested language).

const wait = (ms) => new Promise((r) => setTimeout(r, ms))
const rand = (min, max) => Math.round(min + Math.random() * (max - min))
const pick = (obj, lang) => obj[lang] ?? obj.en

// Simulated network delay so the skeleton loaders are visible
const delay = () => wait(rand(700, 1600))

const STATIONS = [
  { id: 'syntagma',   name: { en: 'Syntagma',    el: 'Σύνταγμα' },    lat: 37.9755, lng: 23.7348 },
  { id: 'patision',   name: { en: 'Patision',    el: 'Πατησίων' },    lat: 37.9999, lng: 23.7333 },
  { id: 'ampelokipi', name: { en: 'Ampelokipoi', el: 'Αμπελόκηποι' }, lat: 37.9874, lng: 23.7569 },
  { id: 'kypseli',    name: { en: 'Kypseli',     el: 'Κυψέλη' },      lat: 38.0010, lng: 23.7430 },
  { id: 'gazi',       name: { en: 'Gazi',        el: 'Γκάζι' },       lat: 37.9780, lng: 23.7120 },
  { id: 'pagrati',    name: { en: 'Pagrati',     el: 'Παγκράτι' },    lat: 37.9680, lng: 23.7480 },
]

// pricePerPerson: average € per person (0 = free). lat/lng = where the event happens.
// popularity: 0–100 score, interested: number of people interested.
const EVENTS = [
  { id: 1, date: '2026-11-29', title: { en: 'Clean-air cycling ride', el: 'Ποδηλατοβόλτα για καθαρό αέρα' }, venue: { en: 'Technopolis', el: 'Τεχνόπολη' }, area: 'gazi', lat: 37.9786, lng: 23.7128, type: { en: 'Community', el: 'Κοινότητα' }, pricePerPerson: 0, popularity: 72, interested: 340 },
  { id: 2, date: '2026-11-25', title: { en: 'Farmers market', el: 'Λαϊκή αγορά παραγωγών' }, venue: { en: 'Fokionos Negri', el: 'Φωκίωνος Νέγρη' }, area: 'kypseli', lat: 37.9985, lng: 23.7395, type: { en: 'Market', el: 'Αγορά' }, pricePerPerson: 12, popularity: 58, interested: 210 },
  { id: 3, date: '2026-12-04', title: { en: 'Christmas tree lighting', el: 'Φωταγώγηση χριστουγεννιάτικου δέντρου' }, venue: { en: 'Syntagma Square', el: 'Πλατεία Συντάγματος' }, area: 'syntagma', lat: 37.9755, lng: 23.7348, type: { en: 'Culture', el: 'Πολιτισμός' }, pricePerPerson: 0, popularity: 96, interested: 4800 },
  { id: 4, date: '2026-12-06', title: { en: 'Jazz night', el: 'Βραδιά τζαζ' }, venue: { en: 'Pagrati', el: 'Παγκράτι' }, area: 'pagrati', lat: 37.9686, lng: 23.7469, type: { en: 'Music', el: 'Μουσική' }, pricePerPerson: 18, popularity: 81, interested: 950 },
  { id: 5, date: '2026-12-12', title: { en: 'Street food festival', el: 'Φεστιβάλ street food' }, venue: { en: 'Gazi', el: 'Γκάζι' }, area: 'gazi', lat: 37.9779, lng: 23.7107, type: { en: 'Food', el: 'Φαγητό' }, pricePerPerson: 15, popularity: 88, interested: 2300 },
]

// Demo EV charging stations in the Municipality of Athens (made-up data)
const EV_STATIONS = [
  { id: 'ev-syntagma', name: { en: 'Syntagma', el: 'Σύνταγμα' }, address: { en: 'Amalias Ave', el: 'Λεωφ. Αμαλίας' }, lat: 37.9741, lng: 23.7363, powerKw: 50, connectors: ['CCS2', 'Type 2'], total: 4, pricePerKwh: 0.49 },
  { id: 'ev-omonia', name: { en: 'Omonia', el: 'Ομόνοια' }, address: { en: 'Athinas St', el: 'Οδός Αθηνάς' }, lat: 37.9838, lng: 23.7281, powerKw: 22, connectors: ['Type 2'], total: 2, pricePerKwh: 0.39 },
  { id: 'ev-kolonaki', name: { en: 'Kolonaki', el: 'Κολωνάκι' }, address: { en: 'Kolonaki Square', el: 'Πλατεία Κολωνακίου' }, lat: 37.9773, lng: 23.7437, powerKw: 22, connectors: ['Type 2'], total: 2, pricePerKwh: 0.42 },
  { id: 'ev-gazi', name: { en: 'Gazi', el: 'Γκάζι' }, address: { en: 'Pireos St', el: 'Οδός Πειραιώς' }, lat: 37.9771, lng: 23.7139, powerKw: 150, connectors: ['CCS2', 'CHAdeMO'], total: 6, pricePerKwh: 0.59 },
  { id: 'ev-ampelokipi', name: { en: 'Ampelokipoi', el: 'Αμπελόκηποι' }, address: { en: 'Alexandras Ave', el: 'Λεωφ. Αλεξάνδρας' }, lat: 37.9905, lng: 23.7545, powerKw: 50, connectors: ['CCS2', 'Type 2'], total: 3, pricePerKwh: 0.49 },
  { id: 'ev-pagrati', name: { en: 'Pagrati', el: 'Παγκράτι' }, address: { en: 'Varnava Square', el: 'Πλατεία Βαρνάβα' }, lat: 37.9663, lng: 23.7448, powerKw: 22, connectors: ['Type 2'], total: 2, pricePerKwh: 0.39 },
]

const stationName = (id, lang) => pick(STATIONS.find((s) => s.id === id).name, lang)

export const mock = {
  // GET /events?lang=
  async getEvents(lang = 'en') {
    await delay()
    return EVENTS.map((e) => ({
      id: e.id,
      date: e.date,
      title: pick(e.title, lang),
      venue: pick(e.venue, lang),
      area: stationName(e.area, lang),
      lat: e.lat,
      lng: e.lng,
      type: pick(e.type, lang),
      category: pick(e.type, lang),
      pricePerPerson: e.pricePerPerson, // € average per person, 0 = free
      currency: 'EUR',
      popularity: e.popularity, // 0–100 popularity rate
      interested: e.interested, // people interested / going
    }))
  },

  // GET /ev/stations?lang=
  // status: 'available' (at least 1 free) | 'busy' (all in use) | 'offline'
  // GET /parking (no sample data: an empty list)
  async getParking() {
    await delay()
    return []
  },

  async getEvStations(lang = 'en') {
    await delay()
    return EV_STATIONS.map((st) => {
      const offline = Math.random() < 0.12
      const available = offline ? 0 : rand(0, st.total)
      return {
        id: st.id,
        name: pick(st.name, lang),
        address: pick(st.address, lang),
        lat: st.lat,
        lng: st.lng,
        powerKw: st.powerKw,
        connectors: st.connectors,
        total: st.total,
        available,
        pricePerKwh: st.pricePerKwh,
        status: offline ? 'offline' : available > 0 ? 'available' : 'busy',
      }
    })
  },

  // GET /ev?history=1
  // occupancy = % of charging points in use, one sample every 10 minutes over the last 24 hours
  async getEvUsage() {
    await delay()
    const curve = (h) => 15 + (h >= 8 && h <= 11 ? 35 : 0) + (h >= 17 && h <= 21 ? 45 : 0) + (h >= 12 && h <= 16 ? 20 : 0)
    const now = Date.now() - (Date.now() % 600000)
    return Array.from({ length: 144 }, (_, i) => {
      const time = now - (143 - i) * 600000
      return { time, occupancy: Math.min(100, curve(new Date(time).getHours()) + rand(-6, 6)) }
    })
  },

  // GET /transit/lines   (public STASY / Hellenic Train timetables, see transitData.js)
  async getTransitLines() {
    await delay()
    return TRANSIT_LINES
  },

  // GET /transit/stations
  async getTransitStations() {
    await delay()
    return TRANSIT_STATIONS
  },

  // POST /agent/chat  body: { message, history, lang }
  async askAgent(message, _history, lang = 'en') {
    await wait(rand(800, 1500))
    const tpl = translations[lang]?.['agent.demoReply'] ?? translations.en['agent.demoReply']
    return { reply: tpl.replace('{q}', message) }
  },
}

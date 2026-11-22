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

// Real, well-known Municipality of Athens venues/places (approximate public coordinates)
const PLACES = [
  { kind: 'museum', name: { en: 'Acropolis Museum', el: 'Μουσείο Ακρόπολης' }, address: { en: 'Dionysiou Areopagitou 15', el: 'Διονυσίου Αρεοπαγίτου 15' }, lat: 37.9683, lng: 23.7283 },
  { kind: 'museum', name: { en: 'National Archaeological Museum', el: 'Εθνικό Αρχαιολογικό Μουσείο' }, address: { en: '44 Patission St', el: 'Πατησίων 44' }, lat: 37.9893, lng: 23.7324 },
  { kind: 'museum', name: { en: 'Benaki Museum', el: 'Μουσείο Μπενάκη' }, address: { en: 'Koumbari 1', el: 'Κουμπάρη 1' }, lat: 37.9797, lng: 23.7439 },
  { kind: 'gallery', name: { en: 'National Gallery', el: 'Εθνική Πινακοθήκη' }, address: { en: 'Vasileos Konstantinou 50', el: 'Λεωφ. Βασιλέως Κωνσταντίνου 50' }, lat: 37.9707, lng: 23.7534 },
  { kind: 'theatre', name: { en: 'National Theatre of Greece', el: 'Εθνικό Θέατρο' }, address: { en: 'Agiou Konstantinou 22', el: 'Αγίου Κωνσταντίνου 22' }, lat: 37.9847, lng: 23.7256 },
  { kind: 'cultural_centre', name: { en: 'Technopolis Gazi', el: 'Τεχνόπολις Γκάζι' }, address: { en: 'Pireos 100', el: 'Πειραιώς 100' }, lat: 37.9786, lng: 23.7121 },
  { kind: 'cultural_centre', name: { en: 'Onassis Stegi', el: 'Στέγη Ιδρύματος Ωνάση' }, address: { en: 'Leof. Syngrou 107', el: 'Λεωφ. Συγγρού 107' }, lat: 37.9636, lng: 23.7363 },
  { kind: 'cultural_centre', name: { en: 'Athens Concert Hall (Megaron)', el: 'Μέγαρο Μουσικής Αθηνών' }, address: { en: 'Vasilissis Sofias & Kokkali 1', el: 'Βασιλισσής Σοφίας & Κόκκαλη 1' }, lat: 37.9752, lng: 23.7638 },
  { kind: 'cultural_centre', name: { en: 'Cultural Centre of the Municipality of Athens', el: 'Πολιτιστικό Κέντρο Δήμου Αθηναίων' }, address: { en: 'Akadimias 50', el: 'Ακαδημίας 50' }, lat: 37.9810, lng: 23.7331 },
  { kind: 'cultural_centre', name: { en: 'Melina Merkouri Cultural Centre', el: 'Πολιτιστικό Κέντρο «Μελίνα»' }, address: { en: 'Irakleidon 66, Thiseio', el: 'Ηρακλειδών 66, Θησείο' }, lat: 37.9756, lng: 23.7166 },
  { kind: 'cultural_centre', name: { en: 'Stavros Niarchos Foundation Cultural Center', el: 'Κέντρο Πολιτισμού Ίδρυμα Σταύρος Νιάρχος' }, address: { en: 'Leof. Syngrou 364, Kallithea', el: 'Λεωφ. Συγγρού 364, Καλλιθέα' }, lat: 37.9399, lng: 23.6918 },
  { kind: 'cultural_centre', name: { en: 'Michael Cacoyannis Foundation', el: 'Ίδρυμα Μιχάλης Κακογιάννης' }, address: { en: 'Pireos 206', el: 'Πειραιώς 206' }, lat: 37.9688, lng: 23.6995 },
  { kind: 'cultural_centre', name: { en: 'Bios', el: 'Bios' }, address: { en: 'Pireos 84', el: 'Πειραιώς 84' }, lat: 37.9783, lng: 23.7180 },
  { kind: 'museum', name: { en: 'Museum of Cycladic Art', el: 'Μουσείο Κυκλαδικής Τέχνης' }, address: { en: 'Neofytou Douka 4', el: 'Νεοφύτου Δούκα 4' }, lat: 37.9762, lng: 23.7449 },
  { kind: 'museum', name: { en: 'Byzantine and Christian Museum', el: 'Βυζαντινό και Χριστιανικό Μουσείο' }, address: { en: 'Vasilissis Sofias 22', el: 'Βασιλίσσης Σοφίας 22' }, lat: 37.9752, lng: 23.7453 },
  { kind: 'museum', name: { en: 'Museum of the City of Athens', el: 'Μουσείο της Πόλεως των Αθηνών' }, address: { en: 'Paparrigopoulou 7', el: 'Παπαρρηγοπούλου 7' }, lat: 37.9790, lng: 23.7311 },
  { kind: 'museum', name: { en: 'Jewish Museum of Greece', el: 'Εβραϊκό Μουσείο Ελλάδος' }, address: { en: 'Nikis 39', el: 'Νίκης 39' }, lat: 37.9727, lng: 23.7334 },
  { kind: 'museum', name: { en: 'National Historical Museum (Old Parliament)', el: 'Εθνικό Ιστορικό Μουσείο (Παλαιά Βουλή)' }, address: { en: 'Stadiou 13', el: 'Σταδίου 13' }, lat: 37.9771, lng: 23.7319 },
  { kind: 'gallery', name: { en: 'National Museum of Contemporary Art (EMST)', el: 'Εθνικό Μουσείο Σύγχρονης Τέχνης (ΕΜΣΤ)' }, address: { en: 'Kallirrois & Frantzi', el: 'Καλλιρρόης & Φραντζή' }, lat: 37.9601, lng: 23.7244 },
  { kind: 'gallery', name: { en: 'Athens Municipal Gallery', el: 'Δημοτική Πινακοθήκη Αθηνών' }, address: { en: 'Leonidou & Myllerou, Metaxourgeio', el: 'Λεωνίδου & Μυλλέρου, Μεταξουργείο' }, lat: 37.9837, lng: 23.7194 },
  { kind: 'theatre', name: { en: 'Odeon of Herodes Atticus', el: 'Ωδείο Ηρώδου του Αττικού' }, address: { en: 'Dionysiou Areopagitou', el: 'Διονυσίου Αρεοπαγίτου' }, lat: 37.9708, lng: 23.7245 },
  { kind: 'theatre', name: { en: 'Pallas Theatre', el: 'Θέατρο Παλλάς' }, address: { en: 'Voukourestiou 5', el: 'Βουκουρεστίου 5' }, lat: 37.9774, lng: 23.7356 },
  { kind: 'theatre', name: { en: 'Olympia Theatre', el: 'Θέατρο Ολύμπια' }, address: { en: 'Akadimias 59', el: 'Ακαδημίας 59' }, lat: 37.9817, lng: 23.7339 },
  { kind: 'cinema', name: { en: 'Cine Thisio', el: 'Σινέ Θησείο' }, address: { en: 'Apostolou Pavlou 7', el: 'Αποστόλου Παύλου 7' }, lat: 37.9724, lng: 23.7189 },
  { kind: 'library', name: { en: 'National Library of Greece', el: 'Εθνική Βιβλιοθήκη της Ελλάδος' }, address: { en: 'Panepistimiou 32', el: 'Πανεπιστημίου 32' }, lat: 37.9838, lng: 23.7325 },
  { kind: 'cinema', name: { en: 'Cine Paris', el: 'Σινε Παρίς' }, address: { en: 'Kydathinaion 22, Plaka', el: 'Κυδαθηναίων 22, Πλάκα' }, lat: 37.9715, lng: 23.7290 },
  { kind: 'place', name: { en: 'Syntagma Square', el: 'Πλατεία Συντάγματος' }, lat: 37.9755, lng: 23.7348 },
  { kind: 'place', name: { en: 'Monastiraki Square', el: 'Πλατεία Μοναστηρακίου' }, lat: 37.9759, lng: 23.7257 },
  { kind: 'place', name: { en: 'Kotzia Square', el: 'Πλατεία Κοτζιά' }, lat: 37.9838, lng: 23.7278 },
  { kind: 'free_wifi', name: { en: 'Syntagma Square Free WiFi', el: 'Δωρεάν WiFi Πλ. Συντάγματος' }, lat: 37.9755, lng: 23.7348 },
  { kind: 'free_wifi', name: { en: 'Thission Free WiFi', el: 'Δωρεάν WiFi Θησείο' }, lat: 37.9723, lng: 23.7205 },
  { kind: 'accessible_parking', name: { en: 'Syntagma accessible parking', el: 'Θέση ΑΜΕΑ Σύνταγμα' }, address: { en: 'Amalias Ave', el: 'Λεωφ. Αμαλίας' }, lat: 37.9745, lng: 23.7355 },
  { kind: 'accessible_parking', name: { en: 'Omonia accessible parking', el: 'Θέση ΑΜΕΑ Ομόνοια' }, address: { en: 'Athinas St', el: 'Οδός Αθηνάς' }, lat: 37.9838, lng: 23.7281 },
  // cool-down spots (Heat page): fountains, pocket parks, pools
  { kind: 'fountain', name: { en: 'Syntagma Square Fountain', el: 'Βρύση Πλ. Συντάγματος' }, lat: 37.9752, lng: 23.7345 },
  { kind: 'pocket_park', name: { en: 'Kypseli Pocket Park', el: 'Πάρκο Τσέπης Κυψέλης' }, lat: 38.0005, lng: 23.7425 },
  { kind: 'pool', name: { en: 'Athens Municipal Pool', el: 'Δημοτικό Κολυμβητήριο Αθηνών' }, lat: 37.9950, lng: 23.7500 },
]

// Sample occupancy curve (% of charging points in use), one point per 10 minutes over the last 24 hours.
// Also shown, labelled as sample data, on the EV page while no real history exists. A smooth daily shape
// (morning rise, midday plateau, evening peak) that depends only on the time of day, so it's stable on refresh.
export function sampleEvUsage() {
  const bump = (t, at, width, height) => height * Math.exp(-(((t - at) / width) ** 2))
  const now = Date.now() - (Date.now() % 600000)
  return Array.from({ length: 144 }, (_, i) => {
    const time = now - (143 - i) * 600000
    const d = new Date(time)
    const t = d.getHours() + d.getMinutes() / 60
    const occupancy = 12 + bump(t, 9.5, 1.8, 30) + bump(t, 14, 2.5, 18) + bump(t, 19, 2, 42) + 2 * Math.sin(t * 1.7)
    return { time, occupancy: Math.round(Math.min(100, Math.max(0, occupancy))) }
  })
}

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
      // no real ticket page for demo events: search link, not a fabricated URL
      url: `https://www.google.com/search?q=${encodeURIComponent(`${pick(e.title, lang)} ${pick(e.venue, lang)}`)}`,
    }))
  },

  // GET /places?lang=
  async getPlaces(lang = 'en') {
    await delay()
    return PLACES.map((p) => ({
      kind: p.kind,
      name: pick(p.name, 'el'), // Greek name, same as the real city GIS
      name_en: pick(p.name, 'en'),
      address: p.address ? pick(p.address, lang) : null,
      lat: p.lat,
      lng: p.lng,
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

  // GET /heat + /zones
  async getHeat() {
    await delay()
    const level = (t) => (t >= 41 ? 'extreme_danger' : t >= 38 ? 'danger' : t >= 35 ? 'extreme_caution' : t >= 32 ? 'caution' : 'none')
    const curve = (h) => 24 + (h >= 11 && h <= 18 ? 10 : 0) + Math.sin((h / 24) * Math.PI * 2) * 3
    const now = Date.now() - (Date.now() % 3600000)
    const hourly = Array.from({ length: 24 }, (_, h) => {
      const t = curve(h) + rand(-1, 1)
      return { time: now - (23 - h) * 3600000, temperature_avg: t, feels_like_avg: t + 2 }
    })
    const cityTemp = hourly[hourly.length - 1].temperature_avg
    return {
      city: { temperature_avg: cityTemp, feels_like_avg: cityTemp + 2, heat_level: level(cityTemp) },
      hourly,
      zones: Array.from({ length: 7 }, (_, i) => {
        const t = cityTemp + rand(-2, 2)
        return { district_id: i + 1, heat: { temperature_avg: t, heat_level: level(t) } }
      }),
    }
  },

  // GET /ev?history=1
  // occupancy = % of charging points in use, one sample every 10 minutes over the last 24 hours
  async getEvUsage() {
    await delay()
    return sampleEvUsage()
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

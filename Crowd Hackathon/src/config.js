// ── Central app settings. Edit freely. ─────────────────────────

// US AQI above this value triggers the in-site push notification
export const AQI_THRESHOLD = 103

// How often to re-fetch air quality (ms)
export const REFRESH_MS = 10 * 60 * 1000

// Municipality of Athens – map is locked to this area.
// NOTE: this is an approximate bounding box. For the exact outline, load the
// municipality GeoJSON (e.g. from geodata.gov.gr) and render it as a <GeoJSON />
// layer in TrafficMap.jsx.
export const ATHENS_CENTER = [37.9838, 23.7275]
export const ATHENS_BOUNDS = [
  [37.955, 23.69], // south-west
  [38.012, 23.785], // north-east
]

// Optional: TomTom traffic tiles for REAL live traffic.
// Create a free key at developer.tomtom.com and put it in .env as VITE_TOMTOM_KEY=xxxx
export const TOMTOM_KEY = import.meta.env.VITE_TOMTOM_KEY || ''

// Sample points used for air-quality readings (one per neighbourhood)
export const DISTRICTS = [
  { id: 'syntagma', name: 'Syntagma', lat: 37.9755, lon: 23.7348 },
  { id: 'exarchia', name: 'Exarchia', lat: 37.9867, lon: 23.7345 },
  { id: 'kypseli', name: 'Kypseli', lat: 38.0, lon: 23.742 },
  { id: 'patisia', name: 'Patisia', lat: 38.0075, lon: 23.729 },
  { id: 'gazi', name: 'Gazi', lat: 37.978, lon: 23.712 },
  { id: 'koukaki', name: 'Koukaki', lat: 37.963, lon: 23.726 },
  { id: 'pagrati', name: 'Pagrati', lat: 37.968, lon: 23.748 },
  { id: 'ampelokipoi', name: 'Ampelokipoi', lat: 37.989, lon: 23.76 },
]

// Main avenues drawn on the traffic layer (approximate centre-lines)
export const CORRIDORS = [
  { id: 'syngrou', name: 'Syngrou Avenue', path: [[37.969, 23.729], [37.96, 23.726], [37.952, 23.722]] },
  { id: 'sofias', name: 'Vasilissis Sofias', path: [[37.9755, 23.7385], [37.978, 23.745], [37.98, 23.756]] },
  { id: 'patission', name: 'Patission Avenue', path: [[37.984, 23.729], [37.9945, 23.73], [38.008, 23.734]] },
  { id: 'alexandras', name: 'Alexandras Avenue', path: [[37.989, 23.733], [37.99, 23.745], [37.9915, 23.756]] },
  { id: 'pireos', name: 'Pireos Street', path: [[37.981, 23.727], [37.978, 23.714], [37.969, 23.702]] },
]

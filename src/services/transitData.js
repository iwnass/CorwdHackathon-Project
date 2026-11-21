/**
 * Athens public transport: timetables + stations.
 *
 * Sources (checked Nov 2026):
 *  - STASY (stasy.gr): Metro Lines 1–3 and Tram first/last departures & frequencies
 *  - OASA / Ministry of Transport: since 13 Sep 2025 Metro Lines 2 & 3 and Tram T6 & T7
 *    run 24 hours every Saturday (Line 1 and Airport trains are NOT included)
 *  - Hellenic Train: Suburban railway (Proastiakos) lines A1–A4. Only the general
 *    operating window is known here, so those times are marked `approx`.
 * Timetables change with works and strikes. The backend can replace this data
 * (see api.getTransitLines / api.getTransitStations).
 *
 * Times are Athens local time, "HH:MM". `last` is per service-day type:
 *   weekday = Mon–Thu & Sun, fri = Friday night, sat = Saturday ('24h' = runs all night)
 */
export const TRANSIT_LINES = [
  // ── Metro ──────────────────────────────────────────────
  {
    id: 'M1', mode: 'metro', label: '1', color: '#00a651',
    route: { en: 'Piraeus – Kifisia', el: 'Πειραιάς – Κηφισιά' },
    first: '05:00', last: { weekday: '00:15', fri: '00:15', sat: '00:15' },
    freq: '5–10', allNightSat: false,
  },
  {
    id: 'M2', mode: 'metro', label: '2', color: '#e2231a',
    route: { en: 'Anthoupoli – Elliniko', el: 'Ανθούπολη – Ελληνικό' },
    first: '05:30', last: { weekday: '00:06', fri: '01:43', sat: '24h' },
    freq: '3–10', satNightFreq: '10–15', allNightSat: true,
  },
  {
    id: 'M3', mode: 'metro', label: '3', color: '#0072bc',
    route: { en: 'Dimotiko Theatro – Doukissis Plakentias', el: 'Δημοτικό Θέατρο – Δουκίσσης Πλακεντίας' },
    first: '05:30', last: { weekday: '23:57', fri: '01:34', sat: '24h' },
    freq: '4–10', satNightFreq: '15', allNightSat: true,
  },
  {
    id: 'M3A', mode: 'metro', label: '3', color: '#0072bc', airport: true,
    route: { en: 'Dimotiko Theatro – Airport', el: 'Δημοτικό Θέατρο – Αεροδρόμιο' },
    first: '05:30', last: { weekday: '22:54', fri: '22:54', sat: '22:54' },
    freq: '36', allNightSat: false,
  },
  // ── Tram ───────────────────────────────────────────────
  {
    id: 'T6', mode: 'tram', label: 'T6', color: '#78be20',
    route: { en: 'Syntagma – Pikrodafni', el: 'Σύνταγμα – Πικροδάφνη' },
    first: '05:30', last: { weekday: '00:50', fri: '00:50', sat: '24h' },
    satNightFreq: '15–25', allNightSat: true,
  },
  {
    id: 'T7', mode: 'tram', label: 'T7', color: '#78be20', viaPikrodafni: true,
    route: { en: 'Asklipieio Voulas – Agia Triada', el: 'Ασκληπιείο Βούλας – Αγία Τριάδα' },
    first: '05:30', last: { weekday: '00:30', fri: '00:30', sat: '24h' },
    satNightFreq: '15–25', allNightSat: true,
  },
  // ── Suburban railway (Proastiakos) ─────────────────────
  {
    id: 'A1', mode: 'suburban', label: 'A1', color: '#f59e0b', approx: true,
    route: { en: 'Piraeus – Athens – Airport', el: 'Πειραιάς – Αθήνα – Αεροδρόμιο' },
    first: '04:30', last: { weekday: '00:00', fri: '00:00', sat: '00:00' }, allNightSat: false,
  },
  {
    id: 'A2', mode: 'suburban', label: 'A2', color: '#f59e0b', approx: true,
    route: { en: 'Ano Liosia – Airport', el: 'Άνω Λιόσια – Αεροδρόμιο' },
    first: '04:30', last: { weekday: '00:00', fri: '00:00', sat: '00:00' }, allNightSat: false,
  },
  {
    id: 'A3', mode: 'suburban', label: 'A3', color: '#f59e0b', approx: true,
    route: { en: 'Athens – Chalkida', el: 'Αθήνα – Χαλκίδα' },
    first: '04:30', last: { weekday: '00:00', fri: '00:00', sat: '00:00' }, allNightSat: false,
  },
  {
    id: 'A4', mode: 'suburban', label: 'A4', color: '#f59e0b', approx: true,
    route: { en: 'Piraeus – Kiato', el: 'Πειραιάς – Κιάτο' },
    first: '04:30', last: { weekday: '00:00', fri: '00:00', sat: '00:00' }, allNightSat: false,
  },
]

/**
 * Stations around central Athens (coordinates approximate, ±100 m).
 * lines = ids/labels shown as coloured badges.
 */
export const TRANSIT_STATIONS = [
  { id: 'syntagma', name: { en: 'Syntagma', el: 'Σύνταγμα' }, lat: 37.9755, lng: 23.7355, lines: ['M2', 'M3', 'T6'] },
  { id: 'monastiraki', name: { en: 'Monastiraki', el: 'Μοναστηράκι' }, lat: 37.9761, lng: 23.7255, lines: ['M1', 'M3'] },
  { id: 'omonia', name: { en: 'Omonia', el: 'Ομόνοια' }, lat: 37.9842, lng: 23.7281, lines: ['M1', 'M2'] },
  { id: 'akropoli', name: { en: 'Akropoli', el: 'Ακρόπολη' }, lat: 37.9688, lng: 23.7295, lines: ['M2'] },
  { id: 'thissio', name: { en: 'Thissio', el: 'Θησείο' }, lat: 37.9767, lng: 23.7206, lines: ['M1'] },
  { id: 'kerameikos', name: { en: 'Kerameikos', el: 'Κεραμεικός' }, lat: 37.9785, lng: 23.7115, lines: ['M3'] },
  { id: 'panepistimio', name: { en: 'Panepistimio', el: 'Πανεπιστήμιο' }, lat: 37.9804, lng: 23.733, lines: ['M2'] },
  { id: 'evangelismos', name: { en: 'Evangelismos', el: 'Ευαγγελισμός' }, lat: 37.9765, lng: 23.747, lines: ['M3'] },
  { id: 'megaro', name: { en: 'Megaro Moussikis', el: 'Μέγαρο Μουσικής' }, lat: 37.9792, lng: 23.7528, lines: ['M3'] },
  { id: 'ambelokipi', name: { en: 'Ambelokipi', el: 'Αμπελόκηποι' }, lat: 37.9873, lng: 23.757, lines: ['M3'] },
  { id: 'metaxourgeio', name: { en: 'Metaxourgeio', el: 'Μεταξουργείο' }, lat: 37.9862, lng: 23.721, lines: ['M2'] },
  { id: 'larissa', name: { en: 'Larissa Station (Athens)', el: 'Σταθμός Λαρίσης (Αθήνα)' }, lat: 37.9917, lng: 23.721, lines: ['M2', 'A1', 'A3', 'A4'] },
  { id: 'viktoria', name: { en: 'Viktoria', el: 'Βικτώρια' }, lat: 37.993, lng: 23.7303, lines: ['M1'] },
  { id: 'attiki', name: { en: 'Attiki', el: 'Αττική' }, lat: 37.9993, lng: 23.7222, lines: ['M1', 'M2'] },
  { id: 'syngrou', name: { en: 'Syngrou-Fix', el: 'Συγγρού-Φιξ' }, lat: 37.9643, lng: 23.7265, lines: ['M2', 'T6'] },
  { id: 'neoskosmos', name: { en: 'Neos Kosmos', el: 'Νέος Κόσμος' }, lat: 37.9576, lng: 23.7286, lines: ['M2', 'T6'] },
  { id: 'zappeio', name: { en: 'Zappeio (tram)', el: 'Ζάππειο (τραμ)' }, lat: 37.9708, lng: 23.7361, lines: ['T6'] },
  { id: 'piraeus', name: { en: 'Piraeus', el: 'Πειραιάς' }, lat: 37.9481, lng: 23.643, lines: ['M1', 'M3', 'A1', 'A4'] },
]

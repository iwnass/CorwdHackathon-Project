// Helpers for the Transit page: Athens time, service status, distances.

const toMin = (hhmm) => {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

// Current Athens weekday (0=Sun … 6=Sat) and minutes since midnight
export function athensNow(date = new Date()) {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Athens',
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  const get = (type) => parts.find((p) => p.type === type)?.value
  const day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(get('weekday'))
  return { day, minutes: Number(get('hour')) * 60 + Number(get('minute')) }
}

// A "service day" starts at 04:00: 01:00 on Saturday still belongs to Friday night.
export function serviceDay({ day, minutes }) {
  return minutes < 240 ? (day + 6) % 7 : day
}

export const dayType = (d) => (d === 5 ? 'fri' : d === 6 ? 'sat' : 'weekday')

export const isSaturday = (now = athensNow()) => serviceDay(now) === 6

/** Last departure for today's service day ('24h' when it runs all night) */
export function lastToday(line, now = athensNow()) {
  return line.last[dayType(serviceDay(now))]
}

/** Is the line running right now? */
export function isRunning(line, now = athensNow()) {
  const sDay = serviceDay(now)
  const last = line.last[dayType(sDay)]
  const first = toMin(line.first)
  const t = now.minutes

  // Saturday all-night: from Saturday's first train until Sunday morning
  // (before 04:00 Sunday still counts as Saturday's service day)
  if (last === '24h') return t >= first || t < 240
  if (line.allNightSat && now.day === 0 && t < first) return true

  let end = toMin(last)
  if (end < first) end += 24 * 60 // last train after midnight
  const tt = t < 240 ? t + 24 * 60 : t
  return tt >= first && tt <= end
}

// Distance in metres (haversine)
export function distanceM(a, b) {
  const R = 6371000
  const rad = (x) => (x * Math.PI) / 180
  const dLat = rad(b.lat - a.lat)
  const dLng = rad(b.lng - a.lng)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

export const walkMinutes = (m) => Math.max(1, Math.round(m / 80)) // ~4.8 km/h

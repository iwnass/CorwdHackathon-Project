// DEMO traffic model.
// Estimates congestion (0–100) from the time of day so the UI is alive without an API key.
// For real data, set VITE_TOMTOM_KEY (see config.js) – the map then shows live TomTom tiles.

const rush = (h, peak, width) => Math.exp(-((h - peak) ** 2) / (2 * width ** 2))

function seeded(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) % 1000
  return h / 1000
}

export function congestionFor(corridorId, date = new Date()) {
  const h = date.getHours() + date.getMinutes() / 60
  const base = 18 + 62 * Math.max(rush(h, 8.75, 1.1), rush(h, 18.25, 1.6) * 0.95)
  const bias = (seeded(corridorId) - 0.5) * 24
  const wobble = Math.sin(date.getMinutes() / 9 + seeded(corridorId) * 10) * 5
  return Math.round(Math.min(98, Math.max(5, base + bias + wobble)))
}

export function congestionLevel(value) {
  if (value < 35) return { label: 'Free flow', hex: '#22c55e', badge: 'bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400' }
  if (value < 60) return { label: 'Moderate', hex: '#eab308', badge: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-400' }
  if (value < 80) return { label: 'Heavy', hex: '#f97316', badge: 'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400' }
  return { label: 'Jammed', hex: '#ef4444', badge: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400' }
}

// US AQI categories. Class strings are written out in full so Tailwind can detect them.
const CATEGORIES = [
  { max: 50, label: 'Good', hex: '#22c55e', badge: 'bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400', bar: 'bg-green-500' },
  { max: 100, label: 'Moderate', hex: '#eab308', badge: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-400', bar: 'bg-yellow-500' },
  { max: 150, label: 'Unhealthy for sensitive groups', short: 'Sensitive groups', hex: '#f97316', badge: 'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400', bar: 'bg-orange-500' },
  { max: 200, label: 'Unhealthy', hex: '#ef4444', badge: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400', bar: 'bg-red-500' },
  { max: 300, label: 'Very unhealthy', hex: '#a855f7', badge: 'bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-400', bar: 'bg-purple-500' },
  { max: Infinity, label: 'Hazardous', hex: '#9f1239', badge: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-400', bar: 'bg-rose-700' },
]

export function getAqiCategory(aqi) {
  const value = Math.round(aqi ?? 0)
  const cat = CATEGORIES.find((c) => value <= c.max)
  return { ...cat, short: cat.short ?? cat.label }
}

export function healthAdvice(aqi) {
  if (aqi <= 50) return 'Air quality is good. Enjoy outdoor activities.'
  if (aqi <= 100) return 'Acceptable. Unusually sensitive people should consider fewer long outdoor efforts.'
  if (aqi <= 150) return 'Children, older adults and people with asthma or heart conditions should limit time outdoors.'
  if (aqi <= 200) return 'Everyone may feel effects. Avoid prolonged outdoor exertion.'
  return 'Health alert. Stay indoors and keep windows closed.'
}

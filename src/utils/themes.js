// Same 6 accent colors as the original kwd-dashboard theme settings.
export const THEME_COLORS = {
  cyan:    { primary: '#06b6d4', light: '#22d3ee', lighter: '#cffafe', dark: '#0891b2', darker: '#155e75' },
  teal:    { primary: '#14b8a6', light: '#2dd4bf', lighter: '#ccfbf1', dark: '#0d9488', darker: '#115e59' },
  green:   { primary: '#22c55e', light: '#4ade80', lighter: '#dcfce7', dark: '#16a34a', darker: '#166534' },
  fuchsia: { primary: '#d946ef', light: '#e879f9', lighter: '#fae8ff', dark: '#c026d3', darker: '#86198f' },
  blue:    { primary: '#3b82f6', light: '#60a5fa', lighter: '#dbeafe', dark: '#2563eb', darker: '#1e40af' },
  violet:  { primary: '#8b5cf6', light: '#a78bfa', lighter: '#ede9fe', dark: '#7c3aed', darker: '#5b21b6' },
}

export const DEFAULT_COLOR = 'cyan'

// Mix two hex colors: t = 0 → a, t = 1 → b. (Canvas/WebGL components need real hex values.)
export function mixHex(a, b, t) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
  const [x, y] = [p(a), p(b)]
  return `#${x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join('')}`
}

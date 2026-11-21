import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { DEFAULT_COLOR, THEME_COLORS } from '../utils/themes'

const ThemeContext = createContext(null)

const read = (key, fallback) => {
  try {
    return localStorage.getItem(key) ?? fallback
  } catch {
    return fallback
  }
}
const write = (key, value) => {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* storage unavailable — ignore */
  }
}

export function ThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(() => document.documentElement.classList.contains('dark'))
  const [color, setColor] = useState(() => {
    const saved = read('color', DEFAULT_COLOR)
    return THEME_COLORS[saved] ? saved : DEFAULT_COLOR
  })
  const [settingsOpen, setSettingsOpen] = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    write('dark', String(isDark))
  }, [isDark])

  useEffect(() => {
    const c = THEME_COLORS[color]
    const root = document.documentElement.style
    root.setProperty('--primary', c.primary)
    root.setProperty('--primary-light', c.light)
    root.setProperty('--primary-lighter', c.lighter)
    root.setProperty('--primary-dark', c.dark)
    root.setProperty('--primary-darker', c.darker)
    write('color', color)
  }, [color])

  const value = useMemo(
    () => ({
      isDark,
      setIsDark,
      toggleDark: () => setIsDark((d) => !d),
      color,
      setColor,
      palette: THEME_COLORS[color], // hex values, used by the charts
      settingsOpen,
      setSettingsOpen,
    }),
    [isDark, color, settingsOpen],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export const useTheme = () => useContext(ThemeContext)

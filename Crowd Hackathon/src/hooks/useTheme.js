import { useEffect, useState } from 'react'

const KEY = 'athens-pulse-theme'

export function useTheme() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try {
      localStorage.setItem(KEY, dark ? 'dark' : 'light')
    } catch {
      /* storage unavailable */
    }
  }, [dark])

  return { dark, toggle: () => setDark((d) => !d) }
}

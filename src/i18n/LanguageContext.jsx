import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { LANG_BY_CODE, LANGUAGES, translations } from './translations'

const LanguageContext = createContext(null)

function initialLang() {
  try {
    const saved = localStorage.getItem('lang')
    if (LANG_BY_CODE[saved]) return saved
  } catch {
    /* ignore */
  }
  // first browser language we support (zh-TW → zh, de-AT → de …)
  for (const l of navigator.languages ?? [navigator.language]) {
    const code = l?.toLowerCase().split('-')[0]
    if (LANG_BY_CODE[code]) return code
  }
  return 'en'
}

// Load a Google Font for Chinese / Japanese / Arabic only when that language is picked
function ensureFont(family) {
  if (!family || document.getElementById(`font-${family}`)) return
  const link = document.createElement('link')
  link.id = `font-${family}`
  link.rel = 'stylesheet'
  link.href = `https://fonts.googleapis.com/css2?family=${family}:wght@400;500;600;700&display=swap`
  document.head.appendChild(link)
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(initialLang)
  const meta = LANG_BY_CODE[lang]

  useEffect(() => {
    const root = document.documentElement
    root.lang = meta.html
    root.dir = meta.dir // Arabic → right-to-left layout
    ensureFont(meta.font)
    try {
      localStorage.setItem('lang', lang)
    } catch {
      /* ignore */
    }
  }, [lang, meta])

  // t('key') or t('key', { q: 'value' }) for "{q}" placeholders
  const t = useCallback(
    (key, vars) => {
      let s = translations[lang][key] ?? translations.en[key] ?? key
      if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v)
      return s
    },
    [lang],
  )

  const value = useMemo(
    () => ({
      lang,
      setLang,
      t,
      languages: LANGUAGES,
      locale: meta.locale, // for dates/numbers: toLocaleString(locale)
      dir: meta.dir,
      mapsLang: meta.maps,
    }),
    [lang, t, meta],
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export const useLang = () => useContext(LanguageContext)

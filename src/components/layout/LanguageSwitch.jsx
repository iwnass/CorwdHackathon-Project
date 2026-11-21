import { useLang } from '../../i18n/LanguageContext'

const GlobeIcon = (p) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
  </svg>
)

/**
 * Language picker (10 languages). A native <select> so it works well with
 * keyboards, screen readers and phone pickers. Each option is written in its
 * own language. `variant="dark"` is for the landing page.
 */
export default function LanguageSwitch({ className = '', variant = 'theme' }) {
  const { lang, setLang, t, languages } = useLang()
  const styles =
    variant === 'dark'
      ? 'bg-[#120f17]/60 text-[#f1ecfa] ring-[#54c7ce]/60 hover:bg-[#652ad0]/50'
      : 'bg-primary/15 text-primary-dark ring-transparent hover:bg-primary/25 dark:text-primary-light'

  return (
    <label className={`relative flex items-center rounded-full ring-1 backdrop-blur transition ${styles} ${className}`}>
      <span className="sr-only">{t('header.language')}</span>
      <GlobeIcon className="pointer-events-none absolute start-2.5 h-4 w-4" />
      <select
        value={lang}
        onChange={(e) => setLang(e.target.value)}
        className="cursor-pointer appearance-none rounded-full bg-transparent py-1.5 pe-7 ps-8 text-sm font-semibold outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        {languages.map((l) => (
          <option key={l.code} value={l.code} lang={l.html} className="bg-white text-gray-900">
            {l.label}
          </option>
        ))}
      </select>
      <svg viewBox="0 0 24 24" className="pointer-events-none absolute end-2.5 h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M6 9l6 6 6-6" />
      </svg>
    </label>
  )
}

import { Link } from 'react-router-dom'
import { useTheme } from '../../context/ThemeContext'
import { useLang } from '../../i18n/LanguageContext'
import GradientText from '../reactbits/GradientText'
import { MoonIcon, SettingsIcon, SunIcon } from '../ui/Icons'
import LanguageSwitch from './LanguageSwitch'

export default function Header() {
  const { isDark, toggleDark, setSettingsOpen, palette } = useTheme()
  const { t } = useLang()

  // Gradient follows the selected theme color
  const gradient = isDark
    ? [palette.light, palette.lighter, palette.primary]
    : [palette.darker, palette.primary, palette.light]

  return (
    <header className="flex items-center justify-between gap-3 border-b border-line bg-surface/80 px-4 py-2.5 backdrop-blur-md">
      <div className="flex items-center gap-2">
        <Link to="/" className="shrink-0 whitespace-nowrap rounded-xl px-1 text-lg font-extrabold tracking-tight sm:text-2xl">
          {/* no border; animationSpeed = seconds per cycle (lower = faster) */}
          <GradientText colors={gradient} animationSpeed={3.5} className="whitespace-nowrap">
            {t('app.name')}
          </GradientText>
        </Link>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <LanguageSwitch className="hidden sm:flex" />

        {/* Dark mode switch (same style as the template) */}
        <button
          onClick={toggleDark}
          role="switch"
          aria-checked={isDark}
          aria-label={t('header.toggleDark')}
          className="relative h-6 w-12 shrink-0 rounded-full bg-primary-lighter transition dark:bg-primary-darker"
        >
          <span
            className={`absolute top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-white text-primary shadow transition-all dark:bg-primary dark:text-white ${
              isDark ? 'left-6.5' : 'left-0.5'
            }`}
          >
            {isDark ? <MoonIcon className="h-3 w-3" /> : <SunIcon className="h-3 w-3" />}
          </span>
        </button>

        <button
          onClick={() => setSettingsOpen(true)}
          className="rounded-md bg-primary/15 p-2 text-primary-dark transition hover:bg-primary hover:text-white dark:text-primary-light"
          aria-label={t('header.settings')}
        >
          <SettingsIcon className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}

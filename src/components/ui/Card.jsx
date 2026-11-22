import { useTheme } from '../../context/ThemeContext'
import { useLang } from '../../i18n/LanguageContext'
import SpotlightCard from '../reactbits/SpotlightCard'

// Glassy card tinted with the theme color (the dot grid shows faintly behind it); a soft glow in the
// accent colour follows the cursor and lights the card's edge (React Bits SpotlightCard).
export function Card({ title, action, children, className = '', bodyClassName = '' }) {
  const { isDark } = useTheme()
  return (
    <SpotlightCard
      theme={isDark ? 'dark' : 'light'}
      spotlightColor="var(--primary-light)"
      intensity={isDark ? 0.22 : 0.5}
      borderGlow={0.9}
      className={`rounded-xl! p-0! bg-surface/85 shadow-sm backdrop-blur-md ${className}`}
      style={{ '--spotlight-card-surface': 'transparent', '--spotlight-card-border': 'var(--line)', '--spotlight-card-shadow': 'none' }}
    >
      <section>
        {title && (
          <header className="flex items-center justify-between border-b border-line px-4 py-2.5">
            <h2 className="text-sm font-semibold text-ink">{title}</h2>
            {action}
          </header>
        )}
        <div className={bodyClassName}>{children}</div>
      </section>
    </SpotlightCard>
  )
}

export function ErrorState({ error, onRetry }) {
  const { t } = useLang()
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 p-4 text-center text-sm text-muted">
      <p>{t('common.error')}</p>
      {import.meta.env.DEV && <p className="text-xs text-red-400">{error?.message}</p>}
      {onRetry && (
        <button onClick={onRetry} className="rounded-md bg-primary px-3 py-1 text-white hover:bg-primary-dark">
          {t('common.retry')}
        </button>
      )}
    </div>
  )
}

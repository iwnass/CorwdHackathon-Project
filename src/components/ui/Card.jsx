import { useLang } from '../../i18n/LanguageContext'

// Glassy card tinted with the theme color (the dot grid shows faintly behind it).
export function Card({ title, action, children, className = '', bodyClassName = '' }) {
  return (
    <section className={`rounded-xl bg-surface/85 shadow-sm ring-1 ring-line backdrop-blur-md ${className}`}>
      {title && (
        <header className="flex items-center justify-between border-b border-line px-4 py-2.5">
          <h2 className="text-sm font-semibold text-ink">{title}</h2>
          {action}
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
    </section>
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

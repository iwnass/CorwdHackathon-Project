import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAthensNow } from '../../hooks/useAthensNow'
import { useLang } from '../../i18n/LanguageContext'
import { isSaturday } from '../../utils/transit'
import { CloseIcon, MoonStarIcon } from '../ui/Icons'
import LineBadge from './LineBadge'

const ALL_NIGHT = ['M2', 'M3', 'T6', 'T7']

/**
 * "Every Saturday the metro runs 24 hours" reminder.
 * variant="card"   → always shown on the Transit page (highlighted on Saturdays)
 * variant="banner" → thin bar on every page, only on Saturdays, can be dismissed
 */
export default function SaturdayReminder({ variant = 'card' }) {
  const { t } = useLang()
  const now = useAthensNow()
  const { pathname } = useLocation()
  const saturday = isSaturday(now)
  const [hidden, setHidden] = useState(() => {
    try {
      return sessionStorage.getItem('satBannerHidden') === '1'
    } catch {
      return false
    }
  })

  if (variant === 'banner') {
    // not on the Transit page: the big card is already there
    if (!saturday || hidden || pathname === '/transit') return null
    return (
      <div className="flex items-center gap-2 border-b border-line bg-primary px-3 py-1.5 text-sm text-white">
        <MoonStarIcon className="h-4 w-4 shrink-0" />
        <Link to="/transit" className="min-w-0 flex-1 truncate font-medium hover:underline">
          {t('transit.satTonight')}
        </Link>
        <span className="hidden gap-1 sm:flex">
          {ALL_NIGHT.map((id) => (
            <LineBadge key={id} id={id} />
          ))}
        </span>
        <button
          onClick={() => {
            setHidden(true)
            try {
              sessionStorage.setItem('satBannerHidden', '1')
            } catch {
              /* ignore */
            }
          }}
          className="rounded p-0.5 hover:bg-white/20"
          aria-label={t('transit.dismiss')}
        >
          <CloseIcon className="h-4 w-4" />
        </button>
      </div>
    )
  }

  return (
    <section
      className={`flex items-start gap-3 rounded-xl p-4 ring-1 ${
        saturday ? 'bg-primary text-white ring-primary shadow-lg shadow-primary/30' : 'bg-surface/85 text-ink ring-line backdrop-blur-md'
      }`}
    >
      <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${saturday ? 'bg-white/20' : 'bg-primary/15 text-primary'}`}>
        <MoonStarIcon className="h-5 w-5" />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="font-semibold">{saturday ? t('transit.satTonight') : t('transit.satTitle')}</h2>
        <p className={`mt-0.5 text-sm ${saturday ? 'text-white/90' : 'text-muted'}`}>{t('transit.satText')}</p>
        <div className="mt-2 flex gap-1.5">
          {ALL_NIGHT.map((id) => (
            <LineBadge key={id} id={id} />
          ))}
        </div>
      </div>
    </section>
  )
}

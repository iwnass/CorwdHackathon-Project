import { NavLink } from 'react-router-dom'
import { config } from '../../config'
import { useLang } from '../../i18n/LanguageContext'
import ChatPanel from '../chat/ChatPanel'
import { CoffeeIcon } from '../ui/Icons'
import { NAV_ITEMS } from './navItems'

/**
 * Side navigation: links on top, the AI chat filling the space in the
 * middle (tablet/desktop), "Buy me a coffee" pinned at the bottom.
 * Tablet / desktop only: on phones the bottom tab bar (BottomNav) replaces it,
 * the chat is the floating button (MobileChat) and "Buy me a coffee" is in Settings.
 */
export default function Sidebar() {
  const { t } = useLang()
  return (
    <nav
      className="hidden w-64 shrink-0 flex-col border-e border-line bg-surface/80 backdrop-blur-md md:flex lg:w-72"
      aria-label={t('nav.main')}
    >
      <ul className="shrink-0 space-y-1 px-3 pt-4">
        {NAV_ITEMS.map(({ to, key, icon: Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-primary text-white shadow-sm shadow-primary/30'
                    : 'text-muted hover:bg-primary/10 hover:text-primary-dark dark:hover:text-primary-light'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              {t(key)}
            </NavLink>
          </li>
        ))}
      </ul>

      {/* AI chat in the sidebar's free space (tablet / desktop) */}
      <div className="mx-3 mt-3 flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl bg-bg/60 ring-1 ring-line">
        <ChatPanel className="flex-1" />
      </div>

      {/* Donate */}
      <div className="p-3">
        <DonateButton />
      </div>
    </nav>
  )
}

// "Buy me a coffee" (also used in the Settings panel on phones)
export function DonateButton() {
  const { t } = useLang()
  return (
    <a
      href={config.donateUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center justify-center gap-2 rounded-lg bg-coffee px-3 py-2.5 text-center text-sm font-semibold text-gray-900 shadow-sm transition hover:brightness-95"
    >
      <CoffeeIcon className="h-5 w-5 shrink-0" />
      {t('nav.donate')}
    </a>
  )
}

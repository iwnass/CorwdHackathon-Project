import { NavLink } from 'react-router-dom'
import { useLang } from '../../i18n/LanguageContext'
import { useNavItems } from './navItems'

// Tab bar at the bottom of the screen on phones (hidden from md up)
export default function BottomNav() {
  const { t } = useLang()
  const items = useNavItems()
  return (
    <nav
      aria-label={t('nav.main')}
      className="shrink-0 border-t border-line bg-surface/90 pb-[env(safe-area-inset-bottom)] backdrop-blur-md md:hidden"
    >
      <ul className="grid auto-cols-fr grid-flow-col">
        {items.map(({ to, key, icon: Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-1 py-2 text-[11px] font-medium transition ${
                  isActive ? 'text-primary' : 'text-muted'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={`rounded-full px-2.5 py-1 transition ${isActive ? 'bg-primary/15' : ''}`}>
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="max-w-full truncate">{t(key)}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}

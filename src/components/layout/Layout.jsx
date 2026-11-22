import { Suspense, useRef } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { useTheme } from '../../context/ThemeContext'
import { useLang } from '../../i18n/LanguageContext'
import { mixHex } from '../../utils/themes'
import MobileChat from '../chat/MobileChat'
import SaturdayReminder from '../transit/SaturdayReminder'
import DotGrid from '../reactbits/DotGrid'
import { PageSkeleton } from '../ui/Skeleton'
import BottomNav from './BottomNav'
import Header from './Header'
import { useNavItems } from './navItems'
import SettingsPanel from './SettingsPanel'
import Sidebar from './Sidebar'

/*
  Tablet / desktop:
  ┌──────────┬───────────────────────────────────────────┐
  │ nav      │ athens pulse (header)                     │
  ├──────────┤───────────────────────────────────────────┤
  │ AI chat  │ page content (map + charts)               │
  │ 🔮 ball  │                                           │
  │ type bar │                                           │
  │ donate   │                                           │
  └──────────┴───────────────────────────────────────────┘
  Phone: header · page · bottom tab bar (no sidebar), AI chat = floating button →
  short bottom sheet, "Buy me a coffee" in Settings.
  Arabic flips the whole layout right-to-left.
  The React Bits Dot Grid sits behind everything, tinted with the theme color.
*/
/*
  Phone tab change: the new page turns in (3D) from the side of the tab you
  tapped. Transit → Events: Events is the tab to the left, so the page comes
  in from the left. Set FROM_TAPPED_SIDE = false to swap the direction.
  Arabic mirrors the tab bar, so the direction mirrors too.
*/
const FROM_TAPPED_SIDE = true

function usePageTurn(pathname, dir) {
  const items = useNavItems()
  const index = items.findIndex((i) => pathname.startsWith(i.to))
  const last = useRef(index)
  const turn = useRef('')
  if (index !== last.current) {
    const toTheRight = index > last.current // tapped tab is to the right (in LTR)
    let fromRight = FROM_TAPPED_SIDE ? toTheRight : !toTheRight
    if (dir === 'rtl') fromRight = !fromRight
    turn.current = fromRight ? 'max-md:animate-turn-from-right' : 'max-md:animate-turn-from-left'
    last.current = index
  }
  return turn.current
}

export default function Layout() {
  const { pathname } = useLocation()
  const { dir } = useLang()
  const turnClass = usePageTurn(pathname, dir)
  const { palette, isDark } = useTheme()

  // Dot colors are derived from the selected theme color
  const baseDot = isDark ? mixHex(palette.primary, '#05070c', 0.68) : mixHex(palette.primary, '#ffffff', 0.62)
  const activeDot = isDark ? palette.light : palette.dark

  return (
    <div className="relative isolate flex h-full bg-bg text-ink transition-colors">
      <div className="fixed inset-0 -z-10" aria-hidden="true">
        <DotGrid
          dotSize={3}
          gap={19}
          proximity={85}
          strength={0.55}
          tension={0.25}
          glow={0.15}
          baseColor={baseDot}
          activeColor={activeDot}
        />
      </div>

      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        {/* Saturdays only: "metro runs all night tonight" */}
        <SaturdayReminder variant="banner" />

        <main className="relative min-h-0 min-w-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-contain p-3 pb-20 [perspective:1400px] sm:p-4 md:px-5 md:pb-6 lg:py-4">
          {/* key = page, so each tab change replays the 3D turn (phones only) */}
          <div key={pathname} className={`origin-center motion-reduce:animate-none ${turnClass}`}>
            <Suspense fallback={<PageSkeleton />}>
              <Outlet />
            </Suspense>
          </div>
        </main>

        <BottomNav />
      </div>

      <MobileChat />
      <SettingsPanel />
    </div>
  )
}

import { useTheme } from '../../context/ThemeContext'
import { EvChargerIcon, EventsIcon, MapPinIcon, SunIcon, TrainIcon } from '../ui/Icons'

// Shared by the sidebar, the mobile bottom tab bar and the landing page buttons
export const NAV_ITEMS = [
  { to: '/events', key: 'nav.events', icon: EventsIcon },
  { to: '/places', key: 'nav.places', icon: MapPinIcon },
  { to: '/transit', key: 'nav.transit', icon: TrainIcon },
  { to: '/ev-charging', key: 'nav.ev', icon: EvChargerIcon },
  { to: '/heat', key: 'nav.heat', icon: SunIcon },
]

// The Heat section can be hidden entirely from Settings ("Heat section" switch)
export function useNavItems() {
  const { showHeatmap } = useTheme()
  return showHeatmap ? NAV_ITEMS : NAV_ITEMS.filter((i) => i.to !== '/heat')
}

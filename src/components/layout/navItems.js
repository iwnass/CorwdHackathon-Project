import { EvChargerIcon, EventsIcon, TrainIcon } from '../ui/Icons'

// Shared by the sidebar, the mobile bottom tab bar and the landing page buttons
export const NAV_ITEMS = [
  { to: '/events', key: 'nav.events', icon: EventsIcon },
  { to: '/transit', key: 'nav.transit', icon: TrainIcon },
  { to: '/ev-charging', key: 'nav.ev', icon: EvChargerIcon },
]

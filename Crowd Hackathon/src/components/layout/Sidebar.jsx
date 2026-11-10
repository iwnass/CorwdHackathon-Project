import { Activity, BellRing, Gauge, Info, LayoutDashboard, Map, X } from 'lucide-react'

// Edit this array to add / rename pages. `href` are in-page anchors for now.
const NAV = [
  { label: 'Overview', icon: LayoutDashboard, href: '#overview' },
  { label: 'Live map', icon: Map, href: '#map' },
  { label: 'Air quality', icon: Gauge, href: '#air' },
  { label: 'Alerts', icon: BellRing, href: '#alerts' },
  { label: 'About', icon: Info, href: '#about' },
]

export function Sidebar({ open, onClose }) {
  return (
    <>
      {/* mobile backdrop */}
      <div
        onClick={onClose}
        className={`fixed inset-0 z-30 bg-black/40 transition-opacity lg:hidden ${open ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
      />

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-gray-200 bg-white transition-transform dark:border-white/5 dark:bg-ink-900 lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex h-16 items-center justify-between px-6">
          <a href="#overview" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary-600 text-white">
              <Activity size={20} />
            </span>
            <span className="text-lg font-bold tracking-tight text-gray-900 dark:text-white">Athens Pulse</span>
          </a>
          <button onClick={onClose} className="rounded-lg p-1 text-gray-500 hover:bg-gray-100 lg:hidden dark:hover:bg-white/10" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">Dashboard</p>
          {NAV.map(({ label, icon: Icon, href }, i) => (
            <a
              key={label}
              href={href}
              onClick={onClose}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                i === 0
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-500/10 dark:text-primary-300'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/5'
              }`}
            >
              <Icon size={18} />
              {label}
            </a>
          ))}
        </nav>

        <div className="m-4 rounded-xl bg-primary-50 p-4 dark:bg-primary-500/10">
          <p className="text-sm font-semibold text-primary-800 dark:text-primary-200">Municipality of Athens</p>
          <p className="mt-1 text-xs leading-relaxed text-primary-700/80 dark:text-primary-300/70">
            Coverage is limited to the municipal area. Built for the apps4athens hackathon.
          </p>
        </div>
      </aside>
    </>
  )
}

import { Bell, BellOff, Menu, Moon, RefreshCw, Sun } from 'lucide-react'
import { Button } from '../ui/Button'

export function Header({ dark, onToggleTheme, onMenu, onRefresh, updatedAt, alertCount, permission, onEnableNotifications }) {
  const time = updatedAt ? updatedAt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '--:--'

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-gray-200 bg-white/80 px-4 backdrop-blur sm:px-6 dark:border-white/5 dark:bg-ink-950/80">
      <Button variant="ghost" size="icon" onClick={onMenu} className="lg:hidden" aria-label="Open menu">
        <Menu size={20} />
      </Button>

      <div className="min-w-0">
        <h1 className="truncate text-lg font-semibold text-gray-900 dark:text-white">City overview</h1>
        <p className="hidden items-center gap-1.5 text-xs text-gray-500 sm:flex dark:text-gray-400">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
          </span>
          Live · updated {time}
        </p>
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        <Button variant="ghost" size="icon" onClick={onRefresh} aria-label="Refresh data" title="Refresh data">
          <RefreshCw size={18} />
        </Button>
        <Button variant="ghost" size="icon" onClick={onToggleTheme} aria-label="Toggle dark mode" title="Toggle dark mode">
          {dark ? <Sun size={18} /> : <Moon size={18} />}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          onClick={permission === 'default' ? onEnableNotifications : undefined}
          aria-label="Notifications"
          title={permission === 'granted' ? 'Browser notifications on' : 'Enable browser notifications'}
        >
          {permission === 'denied' || permission === 'unsupported' ? <BellOff size={18} /> : <Bell size={18} />}
          {alertCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {alertCount}
            </span>
          )}
        </Button>
      </div>
    </header>
  )
}

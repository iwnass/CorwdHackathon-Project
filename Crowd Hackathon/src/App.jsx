import { useEffect, useMemo, useState } from 'react'
import { CORRIDORS, TOMTOM_KEY } from './config'
import { congestionFor } from './lib/traffic'
import { useAirQuality } from './hooks/useAirQuality'
import { useAqiAlerts } from './hooks/useAqiAlerts'
import { useTheme } from './hooks/useTheme'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { ToastStack } from './components/ToastStack'
import Home from './pages/Home'

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [spike, setSpike] = useState(false)
  const [tick, setTick] = useState(0)
  const { dark, toggle } = useTheme()
  const air = useAirQuality()

  // Re-estimate demo traffic every minute
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 60_000)
    return () => clearInterval(id)
  }, [])

  // "Simulate a pollution spike" raises every reading so you can demo the alert
  const districts = useMemo(() => air.districts.map((d) => (spike ? { ...d, aqi: d.aqi + 55 } : d)), [air.districts, spike])
  const corridors = useMemo(() => CORRIDORS.map((c) => ({ ...c, value: congestionFor(c.id) })), [tick])

  const alerts = useAqiAlerts(districts)

  return (
    <div className="min-h-full">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />

      <div className="lg:pl-64">
        <Header
          dark={dark}
          onToggleTheme={toggle}
          onMenu={() => setMenuOpen(true)}
          onRefresh={air.refresh}
          updatedAt={air.updatedAt}
          alertCount={alerts.exceeding.length}
          permission={alerts.permission}
          onEnableNotifications={alerts.requestPermission}
        />
        <main>
          <Home
            air={air}
            districts={districts}
            corridors={corridors}
            dark={dark}
            alerts={alerts}
            spike={spike}
            onToggleSpike={() => setSpike((s) => !s)}
            isTrafficDemo={!TOMTOM_KEY}
          />
        </main>
      </div>

      <ToastStack toasts={alerts.toasts} onDismiss={alerts.dismiss} />
    </div>
  )
}

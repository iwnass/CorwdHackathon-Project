import { Bell, Car, MapPin, Wind } from 'lucide-react'
import { AQI_THRESHOLD } from '../config'
import { getAqiCategory } from '../lib/aqi'
import { congestionLevel } from '../lib/traffic'
import { StatCard } from '../components/ui/StatCard'
import { Badge } from '../components/ui/Badge'
import { AqiAlertBanner } from '../components/AqiAlertBanner'
import { TrafficMap } from '../components/TrafficMap'
import { AqiGauge } from '../components/AqiGauge'
import { AlertSettings } from '../components/AlertSettings'
import { AqiTrendChart } from '../components/AqiTrendChart'
import { DistrictAqiTable } from '../components/DistrictAqiTable'
import { CorridorList } from '../components/CorridorList'
import { Card } from '../components/ui/Card'

export default function Home({ air, districts, corridors, dark, alerts, spike, onToggleSpike, isTrafficDemo }) {
  const avgAqi = districts.length ? Math.round(districts.reduce((s, d) => s + d.aqi, 0) / districts.length) : 0
  const worst = [...districts].sort((a, b) => b.aqi - a.aqi)[0]
  const avgTraffic = Math.round(corridors.reduce((s, c) => s + c.value, 0) / corridors.length)
  const avgCat = getAqiCategory(avgAqi)
  const trafficLvl = congestionLevel(avgTraffic)

  // Keep the last point of the chart in sync with the (possibly simulated) average
  const trend = air.hourly.map((p) => (p.isNow && spike ? { ...p, aqi: avgAqi } : p))

  return (
    <div id="overview" className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6">
      {air.isDemo && (
        <div className="rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-2.5 text-sm text-yellow-800 dark:border-yellow-500/30 dark:bg-yellow-500/10 dark:text-yellow-200">
          Couldn't reach the live air-quality service, showing demo values. ({air.error})
        </div>
      )}

      <AqiAlertBanner exceeding={alerts.exceeding} />

      {/* KPI row */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Wind}
          label="Average AQI"
          value={air.loading ? '–' : avgAqi}
          footer={<Badge className={avgCat.badge}>{avgCat.label}</Badge>}
        />
        <StatCard
          icon={MapPin}
          label="Most polluted area"
          value={worst?.name ?? '–'}
          accent="bg-orange-100 text-orange-600 dark:bg-orange-500/15 dark:text-orange-400"
          footer={worst ? `AQI ${worst.aqi}` : ''}
        />
        <StatCard
          icon={Car}
          label="Traffic congestion"
          value={avgTraffic}
          unit="%"
          accent="bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400"
          footer={<Badge className={trafficLvl.badge}>{trafficLvl.label}</Badge>}
        />
        <StatCard
          icon={Bell}
          label="Active alerts"
          value={alerts.exceeding.length}
          accent={alerts.exceeding.length ? 'bg-red-100 text-red-600 dark:bg-red-500/15 dark:text-red-400' : 'bg-green-100 text-green-600 dark:bg-green-500/15 dark:text-green-400'}
          footer={alerts.exceeding.length ? `Areas above ${AQI_THRESHOLD} AQI` : 'All areas within limits'}
        />
      </section>

      {/* Map + gauge */}
      <section className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <TrafficMap corridors={corridors} districts={districts} dark={dark} />
        </div>
        <div className="space-y-6">
          <AqiGauge aqi={avgAqi} loading={air.loading} />
          <AlertSettings permission={alerts.permission} onEnable={alerts.requestPermission} spike={spike} onToggleSpike={onToggleSpike} />
        </div>
      </section>

      {/* Details */}
      <section className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <AqiTrendChart data={trend} />
        </div>
        <CorridorList corridors={corridors} isDemo={isTrafficDemo} />
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        <DistrictAqiTable districts={districts} />
        <Card id="about" className="p-5 xl:col-span-2">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">About Athens Pulse</h3>
          <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-300">
            Athens Pulse shows live traffic and air quality for the Municipality of Athens. When the US AQI in any
            neighbourhood rises above {AQI_THRESHOLD}, residents get an instant alert on the site so they can limit outdoor
            time. Air-quality data comes from the Open-Meteo Air Quality API (Copernicus CAMS model), refreshed every 10 minutes.
          </p>
          <p className="mt-3 text-xs text-gray-400">Built for the apps4athens hackathon.</p>
        </Card>
      </section>
    </div>
  )
}

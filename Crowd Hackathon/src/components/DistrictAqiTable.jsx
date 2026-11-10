import { AQI_THRESHOLD } from '../config'
import { getAqiCategory } from '../lib/aqi'
import { Card, CardHeader } from './ui/Card'
import { Badge } from './ui/Badge'

export function DistrictAqiTable({ districts }) {
  const sorted = [...districts].sort((a, b) => b.aqi - a.aqi)

  return (
    <Card>
      <CardHeader title="By neighbourhood" subtitle="Sorted by highest AQI" />
      <ul className="divide-y divide-gray-100 px-5 pb-3 pt-2 dark:divide-white/5">
        {sorted.map((d) => {
          const cat = getAqiCategory(d.aqi)
          return (
            <li key={d.id} className="py-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{d.name}</p>
                  <p className="text-xs text-gray-400">PM2.5 {d.pm25.toFixed(1)} · NO₂ {d.no2.toFixed(0)} µg/m³</p>
                </div>
                <Badge className={cat.badge}>{d.aqi}{d.aqi > AQI_THRESHOLD ? ' ⚠' : ''}</Badge>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-white/10">
                <div className={`h-full rounded-full ${cat.bar}`} style={{ width: `${Math.min(100, (d.aqi / 200) * 100)}%` }} />
              </div>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}

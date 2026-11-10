import { TriangleAlert } from 'lucide-react'
import { AQI_THRESHOLD } from '../config'
import { healthAdvice } from '../lib/aqi'

// Sticky banner shown on the page for as long as any district is above the threshold.
export function AqiAlertBanner({ exceeding }) {
  if (!exceeding.length) return null
  const worst = [...exceeding].sort((a, b) => b.aqi - a.aqi)[0]

  return (
    <div role="alert" className="flex items-start gap-3 rounded-2xl border border-orange-200 bg-orange-50 p-4 dark:border-orange-500/30 dark:bg-orange-500/10">
      <TriangleAlert className="mt-0.5 shrink-0 text-orange-600 dark:text-orange-400" size={20} />
      <div className="text-sm">
        <p className="font-semibold text-orange-900 dark:text-orange-200">
          Air quality above {AQI_THRESHOLD} AQI in {exceeding.map((d) => d.name).join(', ')}
        </p>
        <p className="mt-0.5 text-orange-800/90 dark:text-orange-200/80">
          Highest reading: {worst.name} ({worst.aqi}). {healthAdvice(worst.aqi)}
        </p>
      </div>
    </div>
  )
}

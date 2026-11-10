import { AQI_THRESHOLD } from '../config'
import { getAqiCategory, healthAdvice } from '../lib/aqi'
import { Card, CardHeader } from './ui/Card'
import { Badge } from './ui/Badge'

// Half-circle gauge for the city-average AQI (0–300 scale)
const MAX = 300
const R = 80
const C = Math.PI * R // half-circumference

export function AqiGauge({ aqi, loading }) {
  const cat = getAqiCategory(aqi)
  const pct = Math.min(1, aqi / MAX)
  const thresholdAngle = Math.PI * (1 - AQI_THRESHOLD / MAX)
  const tx = 100 + (R + 12) * Math.cos(thresholdAngle)
  const ty = 100 - (R + 12) * Math.sin(thresholdAngle)
  const tx2 = 100 + (R - 12) * Math.cos(thresholdAngle)
  const ty2 = 100 - (R - 12) * Math.sin(thresholdAngle)

  return (
    <Card id="air">
      <CardHeader title="City air quality" subtitle="Average across Athens districts" />
      <div className="px-5 pb-5 pt-2">
        <div className="relative mx-auto w-full max-w-[260px]">
          <svg viewBox="0 0 200 118" className="w-full">
            <path d="M20 100 A80 80 0 0 1 180 100" fill="none" strokeWidth="14" strokeLinecap="round" className="stroke-gray-100 dark:stroke-white/10" />
            <path
              d="M20 100 A80 80 0 0 1 180 100"
              fill="none"
              strokeWidth="14"
              strokeLinecap="round"
              stroke={cat.hex}
              strokeDasharray={`${C * pct} ${C}`}
              style={{ transition: 'stroke-dasharray 0.8s ease, stroke 0.4s' }}
            />
            {/* threshold tick */}
            <line x1={tx} y1={ty} x2={tx2} y2={ty2} strokeWidth="2" className="stroke-gray-800 dark:stroke-white" />
          </svg>
          <div className="absolute inset-x-0 bottom-1 text-center">
            <p className="text-4xl font-bold text-gray-900 dark:text-white">{loading ? '–' : aqi}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">US AQI</p>
          </div>
        </div>
        <div className="mt-4 text-center">
          <Badge className={cat.badge}>{cat.label}</Badge>
          <p className="mt-3 text-sm text-gray-600 dark:text-gray-300">{healthAdvice(aqi)}</p>
          <p className="mt-2 text-xs text-gray-400">Black tick marks the {AQI_THRESHOLD} AQI alert threshold</p>
        </div>
      </div>
    </Card>
  )
}

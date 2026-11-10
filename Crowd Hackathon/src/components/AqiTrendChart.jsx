import { useState } from 'react'
import { AQI_THRESHOLD } from '../config'
import { Card, CardHeader } from './ui/Card'

// Dependency-free SVG line chart: last 24 h + 6 h forecast of the city-average AQI.
const W = 640
const H = 240
const PAD = { top: 16, right: 16, bottom: 28, left: 36 }

export function AqiTrendChart({ data }) {
  const [hover, setHover] = useState(null)
  if (!data.length) return null

  const yMax = Math.max(150, Math.ceil((Math.max(...data.map((d) => d.aqi)) + 10) / 50) * 50)
  const x = (i) => PAD.left + (i / (data.length - 1)) * (W - PAD.left - PAD.right)
  const y = (v) => PAD.top + (1 - v / yMax) * (H - PAD.top - PAD.bottom)

  const line = data.map((d, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(d.aqi).toFixed(1)}`).join(' ')
  const area = `${line} L${x(data.length - 1)} ${y(0)} L${x(0)} ${y(0)} Z`
  const nowIdx = data.findIndex((d) => d.isNow)
  const ticks = [0, yMax / 3, (yMax * 2) / 3, yMax].map(Math.round)
  const hh = (t) => new Date(t).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect()
    const rel = ((e.clientX - r.left) / r.width) * W
    const i = Math.round(((rel - PAD.left) / (W - PAD.left - PAD.right)) * (data.length - 1))
    setHover(Math.min(data.length - 1, Math.max(0, i)))
  }

  return (
    <Card>
      <CardHeader title="AQI – last 24 hours" subtitle="City average, with the next 6 hours forecast" />
      <div className="px-3 pb-4 pt-2 sm:px-5">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
          <defs>
            <linearGradient id="aqi-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" className="[stop-color:var(--color-primary-500)]" stopOpacity="0.28" />
              <stop offset="100%" className="[stop-color:var(--color-primary-500)]" stopOpacity="0" />
            </linearGradient>
          </defs>

          {ticks.map((t) => (
            <g key={t}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} className="stroke-gray-200 dark:stroke-white/10" strokeDasharray="3 4" />
              <text x={PAD.left - 8} y={y(t) + 4} textAnchor="end" className="fill-gray-400 text-[11px]">{t}</text>
            </g>
          ))}

          {/* alert threshold */}
          <line x1={PAD.left} x2={W - PAD.right} y1={y(AQI_THRESHOLD)} y2={y(AQI_THRESHOLD)} stroke="#f97316" strokeWidth="1.5" strokeDasharray="6 4" />
          <text x={W - PAD.right} y={y(AQI_THRESHOLD) - 6} textAnchor="end" fill="#f97316" className="text-[11px] font-medium">Alert {AQI_THRESHOLD}</text>

          <path d={area} fill="url(#aqi-fill)" />
          <path d={line} fill="none" strokeWidth="2.5" strokeLinejoin="round" className="stroke-primary-600 dark:stroke-primary-400" />

          {nowIdx >= 0 && (
            <g>
              <line x1={x(nowIdx)} x2={x(nowIdx)} y1={PAD.top} y2={H - PAD.bottom} className="stroke-gray-300 dark:stroke-white/20" strokeDasharray="2 3" />
              <circle cx={x(nowIdx)} cy={y(data[nowIdx].aqi)} r="5" className="fill-primary-600 stroke-white dark:stroke-ink-900" strokeWidth="2" />
              <text x={x(nowIdx)} y={H - 8} textAnchor="middle" className="fill-gray-500 text-[11px] font-medium">Now</text>
            </g>
          )}

          {[0, Math.floor(data.length / 3), Math.floor((data.length * 2) / 3), data.length - 1].map((i) => (
            i !== nowIdx && <text key={i} x={x(i)} y={H - 8} textAnchor="middle" className="fill-gray-400 text-[11px]">{hh(data[i].time)}</text>
          ))}

          {hover !== null && (
            <g>
              <circle cx={x(hover)} cy={y(data[hover].aqi)} r="4.5" className="fill-white stroke-primary-600" strokeWidth="2.5" />
              <g transform={`translate(${Math.min(x(hover), W - 110)}, ${Math.max(y(data[hover].aqi) - 46, 0)})`}>
                <rect width="100" height="36" rx="8" className="fill-gray-900 dark:fill-white" />
                <text x="50" y="15" textAnchor="middle" className="fill-gray-300 text-[10px] dark:fill-gray-500">{hh(data[hover].time)}</text>
                <text x="50" y="29" textAnchor="middle" className="fill-white text-[12px] font-semibold dark:fill-gray-900">AQI {data[hover].aqi}</text>
              </g>
            </g>
          )}
        </svg>
      </div>
    </Card>
  )
}

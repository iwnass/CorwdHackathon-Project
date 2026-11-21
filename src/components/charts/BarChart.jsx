import { Bar } from 'react-chartjs-2'
import { useChartTheme } from './chartTheme'

/**
 * labels: string[]
 * values: number[]
 * colors: optional per-bar colors (e.g. AQI level colors); default = theme color
 * integer: true for counts (no 0.5 steps on the axis)
 */
export default function BarChart({ labels, values, label = 'Value', colors, integer = false }) {
  const { base, axes, palette } = useChartTheme()
  return (
    <Bar
      data={{
        labels,
        datasets: [
          {
            label,
            data: values,
            backgroundColor: colors ?? palette.light,
            hoverBackgroundColor: colors ?? palette.primary,
            borderRadius: 6,
            maxBarThickness: 36,
          },
        ],
      }}
      options={{
        ...base,
        plugins: { ...base.plugins, legend: { display: false } },
        scales: {
          x: { ...axes.x, ticks: { ...axes.x.ticks, maxRotation: 45, autoSkip: true } },
          y: { ...axes.y, ticks: { ...axes.y.ticks, ...(integer && { precision: 0, stepSize: 1 }) } },
        },
      }}
    />
  )
}

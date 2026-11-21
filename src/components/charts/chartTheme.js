import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { useTheme } from '../../context/ThemeContext'
import { mixHex } from '../../utils/themes'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Filler, Tooltip, Legend)

// Shared chart options that follow dark mode + the selected accent color
export function useChartTheme() {
  const { isDark, palette } = useTheme()
  // axis text + grid lines are tinted with the theme color too
  const text = isDark ? mixHex(palette.light, '#94a3b8', 0.6) : mixHex(palette.darker, '#6b7280', 0.6)
  const grid = isDark ? `${palette.primary}26` : `${palette.primary}1f`

  const base = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 600 },
    plugins: {
      legend: { labels: { color: text, usePointStyle: true, boxWidth: 8 } },
      tooltip: { backgroundColor: isDark ? mixHex(palette.darker, '#05070c', 0.6) : palette.darker, padding: 10, cornerRadius: 6 },
    },
  }
  const axes = {
    x: { ticks: { color: text }, grid: { display: false }, border: { display: false } },
    y: { ticks: { color: text }, grid: { color: grid }, border: { display: false }, beginAtZero: true },
  }

  return { isDark, palette, text, grid, base, axes }
}

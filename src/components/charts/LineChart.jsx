import Chart from 'react-apexcharts'
import ar from 'apexcharts/dist/locales/ar.json'
import de from 'apexcharts/dist/locales/de.json'
import el from 'apexcharts/dist/locales/el.json'
import en from 'apexcharts/dist/locales/en.json'
import es from 'apexcharts/dist/locales/es.json'
import fr from 'apexcharts/dist/locales/fr.json'
import it from 'apexcharts/dist/locales/it.json'
import ja from 'apexcharts/dist/locales/ja.json'
import ru from 'apexcharts/dist/locales/ru.json'
import zhTw from 'apexcharts/dist/locales/zh-tw.json'
import { useTheme } from '../../context/ThemeContext'
import { useLang } from '../../i18n/LanguageContext'

// our language code → ApexCharts locale name (month / day names on the time axis)
const APEX_LOCALES = [en, el, it, de, fr, es, ru, zhTw, ja, ar]
const APEX_NAME = { zh: 'zh-tw' }

/**
 * Line chart built EXACTLY like the kwd-dashboard template's "Line Chart":
 * ApexCharts `area` type, 2 smooth series, legend on top, no grid,
 * no toolbar, datetime x-axis, tooltip "dd/MM/yy HH:mm".
 * Like the template, you can zoom in/out with the mouse wheel and
 * drag to zoom; click a legend item to hide/show that line.
 *
 * props
 *   series:   [{ name, data: [{ x: ISO string | number, y: number }] }]
 *   datetime: true = time axis (default), false = category axis
 */
export default function LineChart({ series, datetime = true }) {
  const { palette, isDark } = useTheme()
  const { lang } = useLang()

  // Template colors: primary-light + violet-light. The first follows the theme;
  // the second stays violet (or cyan when the theme is violet/fuchsia, so the lines differ).
  const second = ['#8b5cf6', '#d946ef'].includes(palette.primary) ? '#22d3ee' : '#a78bfa'

  const options = {
    theme: { mode: isDark ? 'dark' : 'light' },
    colors: [palette.light, second],
    chart: {
      background: 'transparent',
      fontFamily: 'inherit',
      height: '100%',
      width: '100%',
      type: 'area',
      toolbar: { show: false },
      zoom: { enabled: true, type: 'x', allowMouseWheelZoom: true },
      locales: APEX_LOCALES,
      defaultLocale: APEX_NAME[lang] ?? lang,
    },
    legend: { position: 'top' },
    grid: { show: false },
    dataLabels: { enabled: false },
    stroke: { curve: 'smooth' },
    xaxis: {
      type: datetime ? 'datetime' : 'category',
      // hourly category labels (00:00…23:00) would overlap: show ~8, flat
      ...(!datetime && { tickAmount: 8 }),
      labels: { datetimeUTC: false, rotate: 0, hideOverlappingLabels: true },
    },
    tooltip: {
      theme: isDark ? 'dark' : 'light',
      x: { format: 'dd/MM/yy HH:mm' },
    },
  }

  return (
    // key: re-create the chart when language changes so the locale applies
    <Chart key={lang} options={options} series={series} type="area" height="100%" width="100%" />
  )
}

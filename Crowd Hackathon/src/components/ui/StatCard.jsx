import { Card } from './Card'

// KPI tile: icon + label + big value + optional footer line.
// `accent` is a Tailwind class string for the icon bubble.
export function StatCard({ icon: Icon, label, value, unit, footer, accent = 'bg-primary-100 text-primary-600 dark:bg-primary-500/15 dark:text-primary-300' }) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
        <span className={`grid h-10 w-10 place-items-center rounded-xl ${accent}`}>
          <Icon size={20} />
        </span>
      </div>
      <p className="mt-3 text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
        {value}
        {unit && <span className="ml-1 text-base font-medium text-gray-400">{unit}</span>}
      </p>
      {footer && <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">{footer}</div>}
    </Card>
  )
}

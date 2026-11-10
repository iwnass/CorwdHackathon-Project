import { congestionLevel } from '../lib/traffic'
import { Card, CardHeader } from './ui/Card'
import { Badge } from './ui/Badge'

export function CorridorList({ corridors, isDemo }) {
  return (
    <Card>
      <CardHeader title="Main avenues" subtitle={isDemo ? 'Estimated congestion (demo model)' : 'Congestion level'} />
      <ul className="space-y-4 px-5 pb-5 pt-4">
        {corridors.map((c) => {
          const lvl = congestionLevel(c.value)
          return (
            <li key={c.id}>
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900 dark:text-white">{c.name}</span>
                <Badge className={lvl.badge}>{lvl.label}</Badge>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-white/10">
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${c.value}%`, background: lvl.hex }} />
              </div>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}

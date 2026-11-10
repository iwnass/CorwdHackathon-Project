import { BellRing, FlaskConical } from 'lucide-react'
import { AQI_THRESHOLD } from '../config'
import { Card, CardHeader } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'

export function AlertSettings({ permission, onEnable, spike, onToggleSpike }) {
  const status = {
    granted: { tone: 'success', text: 'Enabled' },
    denied: { tone: 'danger', text: 'Blocked in browser' },
    default: { tone: 'neutral', text: 'Not enabled' },
    unsupported: { tone: 'neutral', text: 'Not supported' },
  }[permission]

  return (
    <Card id="alerts">
      <CardHeader title="Air alerts" subtitle={`Notifies when any area exceeds ${AQI_THRESHOLD} AQI`} />
      <div className="space-y-4 px-5 pb-5 pt-4">
        <div className="flex items-center justify-between rounded-xl bg-gray-50 p-3 dark:bg-white/5">
          <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <BellRing size={16} /> Browser notifications
          </div>
          <Badge tone={status.tone}>{status.text}</Badge>
        </div>
        {permission === 'default' && (
          <Button variant="soft" className="w-full" onClick={onEnable}>Enable notifications</Button>
        )}
        <p className="text-xs text-gray-400">In-site alerts always appear. Browser notifications are optional and need your permission.</p>

        {/* Demo helper for the hackathon presentation – remove if you don't need it */}
        <Button variant="outline" size="sm" className="w-full" onClick={onToggleSpike}>
          <FlaskConical size={14} /> {spike ? 'Stop simulation' : 'Simulate a pollution spike'}
        </Button>
      </div>
    </Card>
  )
}

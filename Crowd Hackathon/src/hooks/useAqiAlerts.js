import { useCallback, useEffect, useRef, useState } from 'react'
import { AQI_THRESHOLD } from '../config'

// Watches district readings. When any district goes above the threshold it:
//   1. pushes an in-site toast (always)
//   2. sends a native browser notification (if the visitor allowed it)
// It only re-fires when the set of affected districts changes, so it never spams.
export function useAqiAlerts(districts) {
  const [toasts, setToasts] = useState([])
  const [permission, setPermission] = useState(() => (typeof Notification === 'undefined' ? 'unsupported' : Notification.permission))
  const lastKey = useRef('')

  const dismiss = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), [])

  const requestPermission = useCallback(async () => {
    if (typeof Notification === 'undefined') return
    setPermission(await Notification.requestPermission())
  }, [])

  const exceeding = districts.filter((d) => d.aqi > AQI_THRESHOLD)

  useEffect(() => {
    const key = exceeding.map((d) => d.id).sort().join(',')
    if (key === lastKey.current) return
    lastKey.current = key
    if (!key) return

    const worst = [...exceeding].sort((a, b) => b.aqi - a.aqi)[0]
    const title = 'Air quality alert – Athens'
    const body = `${worst.name} AQI is ${worst.aqi} (limit ${AQI_THRESHOLD}). ${exceeding.length} area${exceeding.length > 1 ? 's' : ''} affected. Limit time outdoors.`

    const id = Date.now()
    setToasts((t) => [...t, { id, title, body }])
    setTimeout(() => dismiss(id), 14000)

    if (permission === 'granted') {
      try {
        new Notification(title, { body, tag: 'athens-pulse-aqi' })
      } catch {
        /* some mobile browsers only allow notifications via service workers */
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exceeding.map((d) => d.id).join(',')])

  return { toasts, dismiss, permission, requestPermission, exceeding }
}

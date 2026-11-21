import { useEffect, useState } from 'react'
import { athensNow } from '../utils/transit'

// Athens day + time, refreshed every minute (for "running now" badges)
export function useAthensNow() {
  const [now, setNow] = useState(athensNow)
  useEffect(() => {
    const id = setInterval(() => setNow(athensNow()), 60_000)
    return () => clearInterval(id)
  }, [])
  return now
}

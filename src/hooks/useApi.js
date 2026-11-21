import { useCallback, useEffect, useState } from 'react'

/**
 * Runs an api.* function and tracks loading / error / data.
 *   const { data, loading, error, reload } = useApi(api.getEvents)
 * Optional: pass `refreshMs` to poll (e.g. live AQI every 5 minutes).
 */
export function useApi(fn, args = [], { refreshMs } = {}) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const key = JSON.stringify(args)

  const load = useCallback(() => {
    let cancelled = false
    setState((s) => ({ ...s, loading: s.data == null, error: null }))
    fn(...args)
      .then((data) => !cancelled && setState({ data, loading: false, error: null }))
      .catch((error) => !cancelled && setState({ data: null, loading: false, error }))
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fn, key])

  useEffect(() => {
    const cancel = load()
    if (!refreshMs) return cancel
    const id = setInterval(load, refreshMs)
    return () => { cancel(); clearInterval(id) }
  }, [load, refreshMs])

  return { ...state, reload: load }
}

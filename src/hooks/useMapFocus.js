import { useCallback, useRef, useState } from 'react'

/**
 * Lets list items (events, EV stations…) point the page's map at a location.
 *   const { mapRef, focus, focusOn, clearFocus } = useMapFocus()
 *   <MapPlaceholder ref={mapRef} focus={focus} onClearFocus={clearFocus} />
 *   <button onClick={() => focusOn({ lat, lng, label })}>📍</button>
 */
export function useMapFocus() {
  const mapRef = useRef(null)
  const [focus, setFocus] = useState(null)

  const focusOn = useCallback((place) => {
    setFocus(place)
    mapRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  const clearFocus = useCallback(() => setFocus(null), [])

  return { mapRef, focus, focusOn, clearFocus }
}

import { useEffect, useRef, useState } from 'react'
import { useLang } from '../../i18n/LanguageContext'

function scrollParent(el) {
  for (let p = el?.parentElement; p; p = p.parentElement) {
    const { overflowY } = getComputedStyle(p)
    if ((overflowY === 'auto' || overflowY === 'scroll') && p.scrollHeight > p.clientHeight + 4) return p
  }
  return null
}

/**
 * Small animated "there's more below" arrow. Place it at the END of a page:
 * it sticks to the bottom of the visible area, fades out once the user
 * scrolls, and scrolls down when clicked. Hidden on phones (they have the tab bar
 * and scroll naturally, and the arrow would cover content).
 */
export default function ScrollHint() {
  const { t } = useLang()
  const ref = useRef(null)
  const [show, setShow] = useState(false)

  useEffect(() => {
    let parent = null
    const update = () => {
      parent = parent || scrollParent(ref.current)
      setShow(!!parent && parent.scrollTop < 40 && parent.scrollHeight > parent.clientHeight + 40)
    }
    // content (charts) appears after loading, so re-check for a short while
    const timers = [100, 600, 1500, 2500].map((ms) => setTimeout(update, ms))
    const onScroll = (e) => {
      if (!parent || e.target === parent) update()
    }
    document.addEventListener('scroll', onScroll, true)
    window.addEventListener('resize', update)
    return () => {
      timers.forEach(clearTimeout)
      document.removeEventListener('scroll', onScroll, true)
      window.removeEventListener('resize', update)
    }
  }, [])

  const scrollDown = () => {
    const p = scrollParent(ref.current)
    p?.scrollBy({ top: p.clientHeight * 0.7, behavior: 'smooth' })
  }

  return (
    <div ref={ref} className="pointer-events-none sticky bottom-3 z-10 hidden h-0 items-end justify-center md:flex">
      <button
        onClick={scrollDown}
        aria-label={t('dash.more')}
        title={t('dash.more')}
        tabIndex={show ? 0 : -1}
        className={`rounded-full bg-surface/90 p-2 text-primary shadow-lg ring-1 ring-line backdrop-blur transition-opacity duration-300 hover:bg-primary hover:text-white ${
          show ? 'pointer-events-auto opacity-100' : 'opacity-0'
        }`}
      >
        <svg viewBox="0 0 24 24" className="h-6 w-6 animate-nudge" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'

/* Extruded title with mouse parallax (landing page) */
const hex = (h, i) => parseInt(h.substr(i, 2), 16)
const mix = (a, b, t) => `rgb(${[1, 3, 5].map((i) => Math.round(hex(a, i) + (hex(b, i) - hex(a, i)) * t)).join(',')})`

export default function DepthText({ text = 'Athens Pulse', faceColor = '#2ac2cc', depthColor = '#652ad0', layers = 14, reach = 26 }) {
  const [p, setP] = useState({ x: 0, y: 0 })
  const target = useRef({ x: 0, y: 0 })
  const current = useRef({ x: 0, y: 0 })

  useEffect(() => {
    let raf
    const onMove = (e) => {
      target.current = {
        x: (e.clientX / window.innerWidth - 0.5) * 2,
        y: (e.clientY / window.innerHeight - 0.5) * 2,
      }
    }
    const tick = () => {
      const c = current.current
      const dx = (target.current.x - c.x) * 0.08
      const dy = (target.current.y - c.y) * 0.08
      // only re-render while the text is still moving
      if (Math.abs(dx) > 0.0005 || Math.abs(dy) > 0.0005) {
        current.current = { x: c.x + dx, y: c.y + dy }
        setP(current.current)
      }
      raf = requestAnimationFrame(tick)
    }
    window.addEventListener('pointermove', onMove)
    raf = requestAnimationFrame(tick)
    return () => {
      window.removeEventListener('pointermove', onMove)
      cancelAnimationFrame(raf)
    }
  }, [])

  const stack = Array.from({ length: layers + 1 }, (_, i) => layers - i) // back to front

  return (
    <h1
      dir="ltr"
      aria-label={text}
      className="relative mx-auto w-fit font-display text-[clamp(2.6rem,11vw,8rem)] font-extrabold leading-none tracking-[-0.02em]"
    >
      {stack.map((i) => {
        const d = i / layers
        const isFace = i === 0
        return (
          <span
            key={i}
            aria-hidden="true"
            className={`block whitespace-nowrap will-change-transform ${isFace ? 'relative' : 'absolute inset-0'}`}
            style={{
              color: isFace ? faceColor : mix(depthColor, '#1b0c3e', d),
              transform: `translate(${-p.x * d * reach}px, ${-p.y * d * reach + d * 10}px)`,
            }}
          >
            {text}
          </span>
        )
      })}
    </h1>
  )
}

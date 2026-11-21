import { useEffect, useRef } from 'react'

/* Animated wave background for the landing page (your original, unchanged logic) */
export default function GradientWaves({ rows = 9, light = 0.12 }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const c = canvasRef.current
    const g = c.getContext('2d')
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let W, H, raf
    let swell = 0
    let mx = -1e4
    let my = -1e4

    const size = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      W = window.innerWidth
      H = window.innerHeight
      c.width = W * dpr
      c.height = H * dpr
      g.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    const onMove = (e) => {
      mx = e.clientX
      my = e.clientY
    }
    const onDown = () => {
      swell = 1
    }
    size()
    window.addEventListener('resize', size)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerdown', onDown)

    const frame = (ts) => {
      const t = ts / 1000
      swell *= 0.95
      g.clearRect(0, 0, W, H)

      const sky = g.createLinearGradient(0, 0, 0, H)
      sky.addColorStop(0, '#120f17')
      sky.addColorStop(0.38, '#241447')
      sky.addColorStop(0.5, '#3b2a6b')
      sky.addColorStop(1, '#120f17')
      g.fillStyle = sky
      g.fillRect(0, 0, W, H)

      const horizon = H * 0.46
      for (let r = 0; r < rows; r++) {
        const k = r / (rows - 1)
        const y0 = horizon + Math.pow(k, 1.6) * (H - horizon) * 0.95
        const amp = 6 + k * 46 + swell * 24
        const freq = 0.004 - k * 0.0021
        const spd = reduce ? 0 : 0.35 + k * 0.5

        g.beginPath()
        g.moveTo(0, H)
        // draw one step past the edge so the wave meets the right side cleanly
        for (let x = 0; x <= W + 8; x += 8) {
          const y =
            y0 +
            Math.sin(x * freq + t * spd + r * 1.7) * amp +
            Math.sin(x * freq * 2.3 - t * spd * 0.8 + r) * amp * 0.35
          g.lineTo(x, y)
        }
        g.lineTo(W, H)
        g.closePath()

        const gr = g.createLinearGradient(0, y0 - amp, 0, y0 + amp * 3 + 60)
        gr.addColorStop(0, `rgba(84,199,206,${0.55 - k * 0.25})`)
        gr.addColorStop(0.35, `rgba(119,48,248,${0.55 - k * 0.1})`)
        gr.addColorStop(1, 'rgba(18,15,23,.95)')
        g.fillStyle = gr
        g.fill()
      }

      // dimmer cursor light (lower `light` prop = darker)
      const R = 220 + swell * 200
      const lg = g.createRadialGradient(mx, my, 0, mx, my, R)
      lg.addColorStop(0, `rgba(190,240,245,${light + swell * 0.08})`)
      lg.addColorStop(1, 'rgba(190,240,245,0)')
      g.globalCompositeOperation = 'lighter'
      g.fillStyle = lg
      g.fillRect(0, 0, W, H)
      g.globalCompositeOperation = 'source-over'

      raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', size)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerdown', onDown)
    }
  }, [rows, light])

  return <canvas ref={canvasRef} aria-hidden="true" className="fixed inset-0 block h-full w-full" />
}

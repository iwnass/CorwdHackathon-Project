import { TRANSIT_LINES } from '../../services/transitData'

const BY_ID = Object.fromEntries(TRANSIT_LINES.map((l) => [l.id, l]))

// Coloured badge for a metro / tram / suburban line (official line colours)
export default function LineBadge({ id, line = BY_ID[id], size = 'sm' }) {
  if (!line) return null
  const round = line.mode === 'metro'
  const dims = size === 'lg' ? 'h-8 min-w-8 text-sm' : 'h-5 min-w-5 text-[11px]'
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center px-1 font-bold leading-none text-white ${dims} ${round ? 'rounded-full' : 'rounded-md'}`}
      style={{ background: line.color }}
    >
      {line.label}
    </span>
  )
}

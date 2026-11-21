/* Faint Parthenon behind the landing title (from your updated Home.jsx) */
export default function ParthenonBackdrop() {
  return (
    <svg
      viewBox="0 14 100 76"
      aria-hidden="true"
      className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-auto w-[clamp(260px,48vw,640px)] -translate-x-1/2 -translate-y-[78%] opacity-30 drop-shadow-[0_0_18px_rgba(143,211,224,0.35)]"
    >
      <g fill="#f4efe6">
        <polygon points="14,40 50,20 86,40" />
        <rect x="16" y="42" width="68" height="5" />
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <rect key={i} x={19 + i * 11.4} y="49" width="6" height="26" />
        ))}
        <rect x="14" y="76" width="72" height="4" />
        <rect x="10" y="81" width="80" height="4" />
      </g>
    </svg>
  )
}

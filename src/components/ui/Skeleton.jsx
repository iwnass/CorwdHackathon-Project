// Generic pulsing block, tinted with the theme color. Use className to size it.
export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-md bg-skel ${className}`} />
}

// Placeholder that looks like a bar chart while data loads
export function ChartSkeleton({ bars = 8 }) {
  const heights = [55, 80, 40, 90, 65, 75, 35, 60, 85, 50]
  return (
    <div className="flex h-full animate-pulse items-end gap-3 px-2 pb-2" aria-busy="true">
      {Array.from({ length: bars }, (_, i) => (
        <div key={i} className="flex-1 rounded-t-md bg-skel" style={{ height: `${heights[i % heights.length]}%` }} />
      ))}
    </div>
  )
}

// Placeholder for the Comet Dial (an open ring)
export function DialSkeleton() {
  return (
    <div className="flex h-full animate-pulse flex-col items-center justify-center gap-3" aria-busy="true">
      <div className="aspect-square h-[70%] rounded-full border-[10px] border-skel border-b-transparent" />
      <div className="h-3 w-24 rounded bg-skel" />
    </div>
  )
}

// Placeholder for list rows
export function ListSkeleton({ rows = 4 }) {
  return (
    <div className="space-y-4" aria-busy="true">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 shrink-0 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-2/3" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        </div>
      ))}
    </div>
  )
}

// Whole-page fallback, shown while a page's code is loading (React.lazy)
export function PageSkeleton() {
  return (
    <div className="space-y-5">
      <Skeleton className="h-[clamp(220px,36vh,380px)] w-full rounded-xl" />
      <div className="grid gap-5 lg:grid-cols-3">
        <Skeleton className="h-64 rounded-xl lg:col-span-2" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    </div>
  )
}

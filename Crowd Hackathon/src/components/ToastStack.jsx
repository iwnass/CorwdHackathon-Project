import { TriangleAlert, X } from 'lucide-react'

// The in-site "push notification". Appears top-right when AQI crosses the threshold.
export function ToastStack({ toasts, onDismiss }) {
  return (
    <div className="pointer-events-none fixed right-4 top-20 z-[2000] flex w-[calc(100vw-2rem)] max-w-sm flex-col gap-3">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className="animate-toast-in pointer-events-auto flex gap-3 rounded-2xl border border-orange-200 bg-white p-4 shadow-xl dark:border-orange-500/30 dark:bg-ink-800"
        >
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-orange-100 text-orange-600 dark:bg-orange-500/15 dark:text-orange-400">
            <TriangleAlert size={20} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-white">{t.title}</p>
            <p className="mt-0.5 text-sm text-gray-600 dark:text-gray-300">{t.body}</p>
          </div>
          <button onClick={() => onDismiss(t.id)} className="h-fit rounded-md p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-white/10" aria-label="Dismiss">
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useLang } from '../../i18n/LanguageContext'
import { CloseIcon, SparklesIcon } from '../ui/Icons'
import ChatPanel from './ChatPanel'

// Phones only (below md): floating button → chat slides up as a bottom sheet.
// On md+ the chat lives in the sidebar instead.
export default function MobileChat() {
  const { t } = useLang()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <div className="md:hidden">
      <button
        onClick={() => setOpen(true)}
        aria-label={t('agent.open')}
        className={`fixed bottom-20 end-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white shadow-lg shadow-primary/40 transition ${
          open ? 'scale-0' : 'scale-100'
        }`}
      >
        <span className="absolute inset-0 animate-ping rounded-full bg-primary opacity-20" />
        <SparklesIcon className="relative h-5 w-5" />
      </button>

      <div
        onClick={() => setOpen(false)}
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity ${open ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
      />

      <div
        className={`fixed inset-x-0 bottom-0 z-50 flex max-h-[min(60dvh,520px)] flex-col rounded-t-2xl bg-surface shadow-2xl ring-1 ring-line transition-transform duration-300 ${
          open ? 'translate-y-0' : 'translate-y-full'
        }`}
        inert={!open}
      >
        {/* top row: drag handle + close */}
        <div className="relative flex h-9 shrink-0 items-center justify-center">
          <span className="h-1.5 w-10 rounded-full bg-line" />
          <button
            onClick={() => setOpen(false)}
            className="absolute end-2 top-1 rounded-md p-1.5 text-muted hover:text-ink"
            aria-label={t('agent.close')}
          >
            <CloseIcon className="h-5 w-5" />
          </button>
        </div>
        <ChatPanel autoFocus={open} ballSize="h-12 w-12" className="min-h-0 flex-1" />
      </div>
    </div>
  )
}

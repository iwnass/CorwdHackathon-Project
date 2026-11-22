import { useEffect, useRef, useState } from 'react'
import { useChat } from '../../context/ChatContext'
import { useTheme } from '../../context/ThemeContext'
import { useLang } from '../../i18n/LanguageContext'
import CrystalizedBall from '../reactbits/CrystalizedBall'
import { CloseIcon, SendIcon } from '../ui/Icons'

/**
 * The AI chat: conversation on top, then the crystal ball sitting right
 * above the type bar (so it "talks" from where you type).
 * Used in the desktop sidebar and in the mobile bottom sheet.
 */

// The assistant's replies use "**bold**" and "- Title: details" (from our own
// local answers and from the AthensGov bot) — render the bold and put the
// details on their own line instead of showing literal asterisks inline.
function formatContent(text) {
  const withLineBreak = text.replace(/^(-\s*)?\*\*(.+?)\*\*:\s*/gm, (_, dash = '', title) => `${dash}**${title}**\n`)
  return withLineBreak.split('\n').flatMap((line, i) => {
    const parts = line.split(/\*\*(.+?)\*\*/g).map((part, j) => (j % 2 === 1 ? <strong key={`${i}-${j}`}>{part}</strong> : part))
    return i === 0 ? parts : [<br key={`br-${i}`} />, ...parts]
  })
}
export default function ChatPanel({ onClose, autoFocus = false, ballSize = 'h-16 w-16', className = '' }) {
  const { t } = useLang()
  const { palette, isDark } = useTheme()
  const { messages, thinking, send } = useChat()
  const [input, setInput] = useState('')
  const listRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  useEffect(() => {
    if (!autoFocus) return
    const id = setTimeout(() => inputRef.current?.focus({ preventScroll: true }), 300)
    return () => clearTimeout(id)
  }, [autoFocus])

  const submit = (text) => {
    if (!text.trim() || thinking) return
    send(text)
    setInput('')
  }

  return (
    <section aria-label={t('agent.name')} className={`relative flex min-h-0 flex-col ${className}`}>
      {onClose && (
        <div className="absolute end-2 top-2 z-10">
          <button onClick={onClose} className="rounded-md p-1.5 text-muted hover:text-ink" aria-label={t('agent.close')}>
            <CloseIcon className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Conversation */}
      <div ref={listRef} className="min-h-0 flex-1 space-y-2 overflow-y-auto px-3 py-2" aria-live="polite">
        {messages.length === 0 && (
          <div className="flex min-h-full flex-col justify-end gap-1.5">
            {['agent.s1', 'agent.s2', 'agent.s3'].map((k) => (
              <button
                key={k}
                onClick={() => submit(t(k))}
                className="rounded-lg border border-line bg-surface/60 px-2.5 py-1.5 text-start text-xs text-muted transition hover:border-primary hover:bg-primary/10 hover:text-primary-dark dark:hover:text-primary-light"
              >
                {t(k)}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <p
              className={`max-w-[90%] whitespace-pre-wrap break-words rounded-2xl px-3 py-1.5 text-sm ${
                m.role === 'user'
                  ? 'rounded-ee-sm bg-primary text-white'
                  : m.error
                    ? 'rounded-es-sm bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300'
                    : 'rounded-es-sm bg-surface-2 text-ink'
              }`}
            >
              {formatContent(m.content)}
            </p>
          </div>
        ))}

        {thinking && (
          <div className="flex gap-1 px-2 py-1" aria-label={t('agent.typing')}>
            {[0, 150, 300].map((d) => (
              <span key={d} className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: `${d}ms` }} />
            ))}
          </div>
        )}
      </div>

      {/* Crystal ball right above the type bar */}
      <div className="flex flex-col items-center px-3 pt-1">
        <div className={`${ballSize} transition-transform duration-500 ${thinking ? 'scale-110' : ''}`} aria-hidden="true">
          <CrystalizedBall
            color={isDark ? palette.light : palette.primary}
            theme={isDark ? 'dark' : 'light'}
            size={0.95}
            particleCount={4000}
            speed={thinking ? 2.2 : 1}
            glow={thinking ? 1.2 : 0.9}
          />
        </div>
        <p className="text-sm font-semibold leading-tight text-ink">{t('agent.name')}</p>
        <p className="text-center text-[11px] leading-snug text-muted">{thinking ? t('agent.thinking') : t('agent.subtitle')}</p>
      </div>

      {/* Type bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit(input)
        }}
        className="p-2.5 pb-[max(0.625rem,env(safe-area-inset-bottom))] md:pb-2.5"
      >
        <label className="flex items-center gap-2 rounded-full bg-bg py-1.5 pe-1.5 ps-3.5 ring-1 ring-line focus-within:ring-2 focus-within:ring-primary">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('agent.placeholder')}
            className="min-w-0 flex-1 bg-transparent text-base text-ink outline-none placeholder:text-muted md:text-sm"
          />
          <button
            type="submit"
            disabled={!input.trim() || thinking}
            className="rounded-full bg-primary p-2 text-white transition hover:bg-primary-dark disabled:opacity-40"
            aria-label={t('agent.send')}
          >
            <SendIcon className="h-3.5 w-3.5 rtl:-scale-x-100" />
          </button>
        </label>
      </form>
    </section>
  )
}

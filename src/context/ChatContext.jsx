import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { useLang } from '../i18n/LanguageContext'
import { api } from '../services/api'

// Conversation state shared by the desktop sidebar chat and the mobile chat sheet
const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const { t, lang } = useLang()
  const [messages, setMessages] = useState([])
  const [thinking, setThinking] = useState(false)

  const send = useCallback(
    async (text) => {
      const message = text.trim()
      if (!message || thinking) return
      const history = messages
      setMessages((m) => [...m, { role: 'user', content: message }])
      setThinking(true)
      try {
        const { reply } = await api.askAgent(message, history, lang)
        setMessages((m) => [...m, { role: 'assistant', content: reply }])
      } catch {
        setMessages((m) => [...m, { role: 'assistant', content: t('agent.error'), error: true }])
      } finally {
        setThinking(false)
      }
    },
    [messages, thinking, lang, t],
  )

  const value = useMemo(() => ({ messages, thinking, send }), [messages, thinking, send])
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export const useChat = () => useContext(ChatContext)

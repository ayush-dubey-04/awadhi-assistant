import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble.jsx'
import { sendChatMessage } from '../api.js'

export default function ChatWindow({ district }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || sending) return

    setMessages((prev) => [...prev, { role: 'user', text: trimmed, matches: [] }])
    setInput('')
    setSending(true)
    setError(null)

    try {
      const data = await sendChatMessage(trimmed, district)
      setMessages((prev) => [...prev, {
        role: 'assistant',
        text: data.reply,
        matches: data.matched_entries,
        source: data.source,
        caveat: data.caveat,
      }])
    } catch (err) {
      setError('Could not reach the backend. Is the FastAPI server running on port 8000?')
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <main className="chat-area" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            शुरू करौ — try a greeting like "namaste", or ask about a word/proverb.<br />
            Try: <em>tohar</em>, <em>your</em>, or "what you sow you reap"
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} text={m.text} matches={m.matches} source={m.source} caveat={m.caveat} />
        ))}
        {sending && (
          <div className="bubble-row assistant">
            <div className="bubble assistant devanagari">…</div>
          </div>
        )}
        {error && <div className="empty-state" style={{ color: '#a6502e' }}>{error}</div>}
      </main>
      <form className="composer" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Type in Awadhi, Hindi, or English (${district})`}
          disabled={sending}
        />
        <button type="submit" disabled={sending || !input.trim()}>Send</button>
      </form>
    </>
  )
}

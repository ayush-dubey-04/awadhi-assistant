import { useState } from 'react'
import { translateText } from '../api.js'

const LANGS = ['awadhi', 'hindi', 'english']

export default function TranslatePanel({ district }) {
  const [text, setText] = useState('')
  const [sourceLang, setSourceLang] = useState('english')
  const [targetLang, setTargetLang] = useState('awadhi')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!text.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await translateText(text, sourceLang, targetLang, district)
      setResult(data)
    } catch (err) {
      setError('Could not reach the backend.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <form className="translate-form" onSubmit={handleSubmit}>
        <div className="lang-row">
          <select value={sourceLang} onChange={(e) => setSourceLang(e.target.value)}>
            {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
          <span aria-hidden="true">→</span>
          <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
            {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <textarea
          className="devanagari"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Text to translate…"
          rows={3}
        />
        <button type="submit" disabled={loading || !text.trim()}>
          {loading ? 'Translating…' : 'Translate'}
        </button>
      </form>

      {error && <div className="empty-state" style={{ color: '#a6502e' }}>{error}</div>}

      {result && result.source === 'llm_unavailable' && (
        <div className="empty-state">{result.caveat}</div>
      )}

      {result && result.source === 'llm_generated' && (
        <div className="result-card">
          <div className="devanagari result-text">{result.translation}</div>
          {result.glossary_hits.length > 0 && (
            <div className="match-tags">
              {result.glossary_hits.map((g, i) => (
                <span key={i} className="match-tag word">verified: {g.awadhi}</span>
              ))}
            </div>
          )}
          <div className="source-note unverified">⚠ {result.caveat}</div>
        </div>
      )}
    </div>
  )
}

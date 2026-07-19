import { useEffect, useState } from 'react'
import { fetchVerses, explainText } from '../api.js'

export default function LiteraturePanel() {
  const [verses, setVerses] = useState([])
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchVerses().then(setVerses).catch(() => setError('Could not load verses.'))
  }, [])

  async function handleExplain(e) {
    e.preventDefault()
    if (!query.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await explainText(query)
      setResult(data)
    } catch (err) {
      setError('Could not reach the backend.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h3 className="panel-heading">Verified verses</h3>
      {verses.map((v) => (
        <div key={v.id} className="verse-card">
          <div className="devanagari verse-text">{v.source_text}</div>
          <div className="verse-transliteration">{v.transliteration}</div>
          <div className="verse-meaning">{v.english_meaning}</div>
          <div className="verse-source">{v.work} · {v.kanda}</div>
        </div>
      ))}

      <h3 className="panel-heading">Ask about a verse or excerpt</h3>
      <form className="translate-form" onSubmit={handleExplain}>
        <textarea
          className="devanagari"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Paste a verse or describe what you're asking about…"
          rows={3}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Explaining…' : 'Explain'}
        </button>
      </form>

      {error && <div className="empty-state" style={{ color: '#a6502e' }}>{error}</div>}

      {result && (
        <div className="result-card">
          <div>{result.explanation}</div>
          {result.source === 'verified_verse_match' && (
            <div className="source-note verified">✓ matched a verified verse</div>
          )}
          {result.source === 'llm_generated' && (
            <div className="source-note unverified">⚠ {result.caveat}</div>
          )}
        </div>
      )}
    </div>
  )
}

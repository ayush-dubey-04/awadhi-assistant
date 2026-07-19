export default function MessageBubble({ role, text, matches = [], source, caveat }) {
  return (
    <div className={`bubble-row ${role}`}>
      <div className={`bubble ${role} devanagari`}>
        <div>{text}</div>
        {matches.length > 0 && (
          <div className="match-tags">
            {matches.map((m) => (
              <span key={m.id} className={`match-tag ${m.type}`}>
                {m.type} · {m.district}
              </span>
            ))}
          </div>
        )}
        {source === 'knowledge_base_lookup' && matches.length > 0 && (
          <div className="source-note verified">✓ verified knowledge base</div>
        )}
        {source === 'llm_generated' && (
          <div className="source-note unverified">⚠ AI-generated, unverified — {caveat}</div>
        )}
      </div>
    </div>
  )
}

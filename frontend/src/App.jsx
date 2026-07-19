import { useEffect, useState } from 'react'
import DistrictSelector from './components/DistrictSelector.jsx'
import ChatWindow from './components/ChatWindow.jsx'
import TranslatePanel from './components/TranslatePanel.jsx'
import LiteraturePanel from './components/LiteraturePanel.jsx'
import { fetchDistricts, fetchModelStatus } from './api.js'

const TABS = ['Chat', 'Translate', 'Literature']

export default function App() {
  const [districts, setDistricts] = useState(['General Awadh'])
  const [district, setDistrict] = useState('General Awadh')
  const [apiError, setApiError] = useState(false)
  const [modelStatus, setModelStatus] = useState(null)
  const [activeTab, setActiveTab] = useState('Chat')

  useEffect(() => {
    fetchDistricts()
      .then((list) => setDistricts(list))
      .catch(() => setApiError(true))
    fetchModelStatus()
      .then(setModelStatus)
      .catch(() => setModelStatus(null))
  }, [])

  return (
    <div className="app-shell">
      <div className="motif-band" aria-hidden="true" />
      <header className="app-header">
        <h1>चौपाल <span style={{ color: '#8a8371', fontFamily: 'Inter', fontSize: '1rem' }}>·</span> Awadhi Assistant</h1>
        <p className="tagline">
          Phase 4 — chat, translation, and literature, all knowledge-base first with LLM fallback.
        </p>
        <p className="tagline">
          {modelStatus === null && 'Checking LLM backend…'}
          {modelStatus && modelStatus.ollama_reachable && modelStatus.model_available &&
            `● LLM ready (${modelStatus.configured_model})`}
          {modelStatus && modelStatus.ollama_reachable && !modelStatus.model_available &&
            `○ Ollama running, but model '${modelStatus.configured_model}' not pulled — run: ollama pull ${modelStatus.configured_model}`}
          {modelStatus && !modelStatus.ollama_reachable &&
            '○ Ollama not running — unmatched queries will fall back to a plain message. Run: ollama serve'}
        </p>
        {apiError && (
          <p className="tagline" style={{ color: '#a6502e' }}>
            Backend unreachable at startup. Start it with: uvicorn main:app --reload (in /backend)
          </p>
        )}
        <DistrictSelector districts={districts} selected={district} onSelect={setDistrict} />
        <div className="tab-row" role="tablist">
          {TABS.map((t) => (
            <button
              key={t}
              type="button"
              role="tab"
              aria-selected={t === activeTab}
              className={`tab-button${t === activeTab ? ' active' : ''}`}
              onClick={() => setActiveTab(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </header>
      {activeTab === 'Chat' && <ChatWindow district={district} />}
      {activeTab === 'Translate' && <TranslatePanel district={district} />}
      {activeTab === 'Literature' && <LiteraturePanel />}
      <p className="phase-note">
        Seed data is illustrative only and has not been verified by native speakers per district.
      </p>
    </div>
  )
}

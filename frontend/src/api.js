const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function handle(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

export async function fetchDistricts() {
  const res = await fetch(`${API_BASE}/knowledge/districts`)
  return handle(res)
}

export async function fetchModelStatus() {
  const res = await fetch(`${API_BASE}/chat/model-status`)
  return handle(res)
}

export async function translateText(text, sourceLang, targetLang, district) {
  const res = await fetch(`${API_BASE}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang, district }),
  })
  return handle(res)
}

export async function fetchVerses() {
  const res = await fetch(`${API_BASE}/literature/verses`)
  return handle(res)
}

export async function explainText(text) {
  const res = await fetch(`${API_BASE}/literature/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return handle(res)
}

export async function sendChatMessage(message, district) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, district }),
  })
  return handle(res)
}

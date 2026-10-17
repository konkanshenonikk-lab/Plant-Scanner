const API_BASE = import.meta.env.DEV ? '/api' : ''

/** Send a leaf image to the FastAPI backend and return the prediction JSON. */
export async function predictImage(file, lang = 'en') {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch(`${API_BASE}/predict?lang=${encodeURIComponent(lang)}`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `Prediction failed (${res.status})`)
  }
  return res.json()
}

/** Translation bundle for one language (UI labels + reason chips). */
export async function getI18n(lang = 'en') {
  const res = await fetch(`${API_BASE}/i18n?lang=${encodeURIComponent(lang)}`)
  if (!res.ok) throw new Error('i18n unavailable')
  return res.json()
}

/** Backend liveness check used by the header badge. */
export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('backend offline')
  return res.json()
}

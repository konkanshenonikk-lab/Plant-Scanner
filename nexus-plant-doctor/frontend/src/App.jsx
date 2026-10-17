import { useCallback, useEffect, useRef, useState } from 'react'
import { getHealth, predictImage } from './api.js'
import { useI18n } from './i18n.jsx'
import ImageUpload from './components/ImageUpload.jsx'
import ResultCard from './components/ResultCard.jsx'
import SampleGallery from './components/SampleGallery.jsx'

const SAMPLES = [
  { key: 'sample_corn', name: 'Corn rust', src: '/samples/corn-rust.jpg' },
  { key: 'sample_potato', name: 'Potato early blight', src: '/samples/potato-early-blight.jpg' },
  { key: 'sample_tomato', name: 'Tomato bacterial spot', src: '/samples/tomato-bacterial.jpg' },
]

export default function App() {
  const { lang, setLang, t } = useI18n()
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [online, setOnline] = useState(false)
  const resultRef = useRef(null)
  // Last analyzed image, kept so a language switch can re-render the verdict
  // in the new language without asking the user to re-upload.
  const lastFileRef = useRef(null)

  useEffect(() => {
    getHealth()
      .then((h) => setOnline(Boolean(h.model_loaded)))
      .catch(() => setOnline(false))
  }, [])

  const analyze = useCallback(
    async (file) => {
      if (!file) return
      if (!file.type.startsWith('image/')) {
        setError(t('err_image', 'Please choose an image file (JPG or PNG).'))
        return
      }
      setError(null)
      setResult(null)
      setPreview(URL.createObjectURL(file))
      setLoading(true)
      try {
        const data = await predictImage(file, lang)
        lastFileRef.current = file
        setResult(data)
        requestAnimationFrame(() =>
          resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }),
        )
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    },
    [lang, t],
  )

  const loadSample = useCallback(
    async (sample) => {
      setLoading(true)
      setError(null)
      setResult(null)
      setPreview(sample.src)
      try {
        const blob = await fetch(sample.src).then((r) => r.blob())
        const file = new File([blob], `${sample.name}.jpg`, { type: 'image/jpeg' })
        const data = await predictImage(file, lang)
        lastFileRef.current = file
        setResult(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    },
    [lang],
  )

  // Language changed after a verdict: re-ask the backend in the new language
  // (silent - keep the preview, don't scroll again).
  useEffect(() => {
    const file = lastFileRef.current
    if (!file || !result) return
    let cancelled = false
    setLoading(true)
    predictImage(file, lang)
      .then((data) => {
        if (!cancelled) setResult(data)
      })
      .catch(() => {}) // keep the old-language result if the re-ask fails
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang])

  const switchLang = () => setLang(lang === 'en' ? 'kn' : 'en')

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            🌿
          </span>
          <div>
            <h1>Nexus Plant Doctor</h1>
            <p className="tagline">{t('tagline', 'CNN crop-disease detection')}</p>
          </div>
        </div>
        <div className="header-side">
          <button
            className="lang-toggle"
            onClick={switchLang}
            aria-label={t('lang_label', 'Language')}
            title={t('lang_label', 'Language')}
          >
            <span className={lang === 'en' ? 'lang-on' : ''}>EN</span>
            <span className="lang-sep">|</span>
            <span className={lang === 'kn' ? 'lang-on' : ''}>ಕನ್ನಡ</span>
          </button>
          <span className={`badge ${online ? 'badge-online' : 'badge-offline'}`}>
            {online ? t('badge_online', '● model online') : t('badge_offline', '● backend offline')}
          </span>
        </div>
      </header>

      <section className="hero">
        <span className="pill">
          {t('pill', '38 disease classes · 14 crop species')}
        </span>
        <h2>
          {t('hero_title_a', 'Diagnose crop disease from a')}{' '}
          <em>{t('hero_title_em', 'single leaf photo')}</em>
        </h2>
        <p>
          {t(
            'hero_body',
            'Upload a picture or snap one with your camera. A convolutional neural network returns the most likely condition, its confidence, and field-level treatment advice.',
          )}
        </p>
      </section>

      <section className="grid">
        <div className="card">
          <ImageUpload onFile={analyze} loading={loading} preview={preview} />
          <SampleGallery samples={SAMPLES} onPick={loadSample} loading={loading} />
        </div>

        <div className="card" ref={resultRef}>
          {loading && (
            <div className="loading" role="status">
              <span className="spinner" />
              <p>{t('loading', 'Analyzing leaf tissue…')}</p>
            </div>
          )}

          {!loading && error && <div className="error">⚠ {error}</div>}

          {!loading && !error && !result && (
            <div className="empty">
              <span className="empty-icon">🔍</span>
              <p>{t('empty', 'The diagnosis will appear here.')}</p>
            </div>
          )}

          {!loading && result && <ResultCard result={result} />}
        </div>
      </section>

      <footer className="footer">
        <p>
          {t(
            'footer',
            'Keras 3 · PyTorch (CUDA) · FastAPI · React + Vite — built from scratch',
          )}
        </p>
      </footer>
    </div>
  )
}

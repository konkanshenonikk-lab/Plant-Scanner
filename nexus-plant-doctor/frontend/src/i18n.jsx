import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { getI18n } from './api.js'

/**
 * Language context: English ⇄ Kannada.
 *
 * The translation tables live in backend/i18n.py (single source of truth) and
 * are served by GET /i18n?lang=kn. Components call t(key, englishFallback) so
 * the English UI keeps working with no bundle at all (e.g. backend offline);
 * the bundle only *overrides* when a translation exists.
 *
 * Choice persists in localStorage; first visit follows the browser language.
 */
const LangContext = createContext(null)

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(
    () =>
      localStorage.getItem('nexus-lang') ||
      (navigator.language?.toLowerCase().startsWith('kn') ? 'kn' : 'en'),
  )
  // { [lang]: { ui: {...}, reasons: {...} } } — populated lazily per language.
  const [bundles, setBundles] = useState({})

  useEffect(() => {
    document.documentElement.lang = lang
    if (bundles[lang]) return
    let cancelled = false
    getI18n(lang)
      .then((data) => {
        if (!cancelled) setBundles((prev) => ({ ...prev, [lang]: data }))
      })
      .catch(() => {
        // Offline: English fallbacks in the components carry the UI.
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang])

  const setLang = (next) => {
    localStorage.setItem('nexus-lang', next)
    setLangState(next)
  }

  const value = useMemo(() => {
    const bundle = bundles[lang]
    /** t('key', 'English default', { param: 1 }) -> translated or default. */
    const t = (key, fallback, params) => {
      let text = bundle?.ui?.[key] ?? fallback ?? key
      if (params) {
        for (const [name, val] of Object.entries(params)) {
          text = text.replaceAll(`{${name}}`, String(val))
        }
      }
      return text
    }
    return { lang, setLang, t, reasons: bundle?.reasons }
  }, [lang, bundles])

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}

export function useI18n() {
  const ctx = useContext(LangContext)
  if (!ctx) throw new Error('useI18n must be used inside <I18nProvider>')
  return ctx
}

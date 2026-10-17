import { useI18n } from '../i18n.jsx'

/** One-click demo leaves so users can try the model without their own photo. */
export default function SampleGallery({ samples, onPick, loading }) {
  const { t } = useI18n()
  return (
    <div className="samples">
      <p className="samples-title">
        {t('samples_title', 'Or try a sample leaf')}
      </p>
      <div className="samples-row">
        {samples.map((sample) => (
          <button
            key={sample.src}
            className="sample"
            disabled={loading}
            onClick={() => onPick(sample)}
          >
            <img src={sample.src} alt={t(sample.key, sample.name)} />
            <span>{t(sample.key, sample.name)}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

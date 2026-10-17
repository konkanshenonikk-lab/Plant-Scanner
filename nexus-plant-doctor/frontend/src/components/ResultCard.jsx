/** Result panel: leaf identification verdict first, then the disease diagnosis. */
import { useI18n } from '../i18n.jsx'

function pct(v) {
  return `${Math.round(v * 100)}%`
}

// English fallback if the /i18n bundle has not loaded yet.
const REASON_TEXT = {
  low_confidence: 'low model confidence',
  high_entropy: 'spread-out probabilities',
  unlike_training_data: 'unlike any training photo',
  no_leaf_texture: 'no leaf texture (flat/synthetic)',
  close_call: 'top candidates too close to call',
  inconsistent: 'the photo answers differently when cropped',
  experts_disagree: 'the two models name different plants',
  model_unavailable: 'identification model unavailable',
  no_signal: 'no reliable signal in this image',
}

function CoveredCrops({ crops }) {
  const { t } = useI18n()
  if (!crops?.length) return null
  return (
    <div className="covered">
      <h5>
        {t('covered_title', 'Crops this model is trained on')} ({crops.length})
      </h5>
      <div className="chips">
        {crops.map((c) => (
          <span className="chip" key={c}>
            {c}
          </span>
        ))}
      </div>
    </div>
  )
}

/** The headline answer to "what is this leaf - and do you actually know?" */
function IdentificationStrip({ ident }) {
  const { t, reasons } = useI18n()
  if (!ident) return null
  const identified = ident.status === 'identified'

  if (identified) {
    return (
      <section className="ident ident-yes">
        <p className="ident-title">
          <span aria-hidden>🌱</span> {t('ident_yes', 'Leaf identified:')}{' '}
          <em>{ident.name}</em>
          {ident.confidence != null && (
            <span className="ident-conf">{pct(ident.confidence)}</span>
          )}
        </p>
        <ul className="ident-evidence">
          {ident.evidence?.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
        {ident.note && <p className="ident-note">{ident.note}</p>}
      </section>
    )
  }

  return (
    <section className="ident ident-no">
      <p className="ident-title">
        <span aria-hidden>❓</span> {t('ident_no', 'Not identified')}
      </p>
      <p className="ident-note">
        {t(
          'ident_no_body',
          'Neither model could prove what plant this is, so no name is given rather than a wrong one.',
        )}
      </p>
      {ident.reasons?.length > 0 && (
        <div className="flagged">
          {t('ident_why', 'Why:')}{' '}
          {ident.reasons.map((r) => (
            <span className="flag-chip" key={r}>
              {reasons?.[r] || REASON_TEXT[r] || r}
            </span>
          ))}
        </div>
      )}
      {ident.conflict && (
        <div className="conflict">
          <p>
            <span className="conflict-model">{t('conflict_crop', 'Crop model')}</span>{' '}
            {t('conflict_says', 'says')}{' '}
            <strong>{ident.conflict.crop_model}</strong>
          </p>
          <p>
            <span className="conflict-model">{t('conflict_species', 'Species model')}</span>{' '}
            {t('conflict_says', 'says')}{' '}
            <strong>{ident.conflict.species_model}</strong>
          </p>
        </div>
      )}
      {ident.best_guess && !ident.conflict && (
        <p className="ident-guess">
          {t('ident_guess', 'Closest guess (unreliable):')}{' '}
          <s>{String(ident.best_guess).replaceAll('_', ' ')}</s>
        </p>
      )}
      <ul className="ident-tips">
        <li>{t('tip_1', 'Fill the frame with a single leaf, in daylight')}</li>
        <li>{t('tip_2', 'Use a plain background and avoid shadows')}</li>
        <li>
          {t(
            'tip_3',
            'Include the leaf edge and underside if spots are only on the back',
          )}
        </li>
      </ul>
    </section>
  )
}

export default function ResultCard({ result }) {
  const { t } = useI18n()
  const {
    status,
    headline,
    identification,
    plant,
    disease,
    confidence,
    healthy,
    advice,
    top_k,
    trust,
    second_model,
    covered_crops,
  } = result

  const notIdentified = status === 'not_identified'
  const identifiedOnly = status === 'identified_only'
  const showDiagnosis = status === 'diagnosed' || status === 'disputed'
  const disputed = status === 'disputed'

  const statusLabel = notIdentified
    ? t('status_not_identified', '❓ Not identified')
    : identifiedOnly
      ? t('status_identified_only', '🌱 Identified (no diagnosis)')
      : disputed
        ? t('status_disputed', '⚠ Conflicting signals')
        : healthy
          ? t('status_healthy', '✅ Healthy')
          : t('status_disease', '🦠 Disease detected')
  const statusClass = notIdentified
    ? 'warn'
    : identifiedOnly
      ? 'healthy'
      : disputed
        ? 'caution'
        : healthy
          ? 'healthy'
          : 'disease'
  const bannerKind = notIdentified ? 'warn' : disputed ? 'caution' : 'ok'

  return (
    <div className={`result ${bannerKind}`}>
      <div className="result-head">
        <span className={`result-status status-${statusClass}`}>{statusLabel}</span>
        {/* Crop badge only where the crop model's claim is the actual verdict;
            for identified_only its claim was overridden by the species model. */}
        {showDiagnosis && <span className="result-crop">{plant}</span>}
      </div>

      <IdentificationStrip ident={identification} />

      {headline && <p className="headline">{headline}</p>}

      {showDiagnosis && (
        <>
          <h3 className="result-diagnosis">{disease}</h3>

          <div className="gauge-row">
            <div className="gauge">
              <div
                className="gauge-fill"
                style={{ width: `${Math.round(confidence * 100)}%` }}
              />
            </div>
            <span className="gauge-label">
              {pct(confidence)} {t('gauge_confidence', 'confidence')}
            </span>
          </div>

          <div className={`trust trust-${trust?.level || 'single'}`}>
            <strong>{trust?.label}</strong>
            {trust?.note && <span> — {trust.note}</span>}
          </div>

          {second_model && (
            <p className="second-line">
              {t('second_line', 'Independent PlantDoc ViT says:')}{' '}
              <strong>
                {second_model.crop ?? second_model.label} —{' '}
                {second_model.disease ?? 'unknown'}
              </strong>{' '}
              ({pct(second_model.confidence)})
            </p>
          )}

          <ul className="topk">
            {top_k.map((item) => (
              <li key={item.class}>
                <span className="topk-label">
                  {item.plant} — {item.disease}
                </span>
                <span className="topk-bar">
                  <span style={{ width: `${Math.round(item.confidence * 100)}%` }} />
                </span>
                <span className="topk-value">{pct(item.confidence)}</span>
              </li>
            ))}
          </ul>

          <div className="advice">
            <h4>{t('advice_title', '💡 Recommended action')}</h4>
            <p>{advice}</p>
          </div>
        </>
      )}

      {identifiedOnly && identification?.alternatives?.length > 0 && (
        <ul className="topk">
          {identification.alternatives.map((alt) => (
            <li key={alt.name}>
              <span className="topk-label">{alt.name}</span>
              <span className="topk-bar">
                <span style={{ width: `${Math.round(alt.confidence * 100)}%` }} />
              </span>
              <span className="topk-value">{pct(alt.confidence)}</span>
            </li>
          ))}
        </ul>
      )}

      <CoveredCrops crops={covered_crops} />

      <p className="disclaimer">
        {t(
          'disclaimer',
          'AI-generated diagnosis — confirm with a local agronomist before applying chemicals.',
        )}
      </p>
    </div>
  )
}

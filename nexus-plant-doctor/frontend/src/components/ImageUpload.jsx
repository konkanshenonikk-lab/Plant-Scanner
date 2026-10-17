import { useCallback, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import CameraModal from './CameraModal.jsx'
import { useI18n } from '../i18n.jsx'

/** Drag-and-drop uploader with click-to-browse and live camera capture. */
export default function ImageUpload({ onFile, loading, preview }) {
  const { t } = useI18n()
  const [dragging, setDragging] = useState(false)
  const [cameraOpen, setCameraOpen] = useState(false)
  const inputRef = useRef(null)
  const cameraFallbackRef = useRef(null)

  const handleDrop = useCallback(
    (event) => {
      event.preventDefault()
      setDragging(false)
      const file = event.dataTransfer.files?.[0]
      if (file) onFile(file)
    },
    [onFile],
  )

  const openCamera = useCallback(() => {
    if (navigator.mediaDevices?.getUserMedia) {
      setCameraOpen(true)
    } else {
      // Old mobile browsers: hand off to the native camera app instead.
      cameraFallbackRef.current?.click()
    }
  }, [])

  const handleCapture = useCallback(
    (file) => {
      setCameraOpen(false)
      onFile(file)
    },
    [onFile],
  )

  return (
    <div className="upload">
      <div
        className={`dropzone ${dragging ? 'dropzone-active' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        {preview ? (
          <img
            className="preview"
            src={preview}
            alt={t('alt_selected_leaf', 'Selected leaf')}
          />
        ) : (
          <>
            <span className="dropzone-icon" aria-hidden="true">
              🍃
            </span>
            <p className="dropzone-title">
              {t('drop_title', 'Drop a leaf photo here')}
            </p>
            <p className="dropzone-sub">
              {t('drop_sub', 'or click to browse · JPG / PNG · max 8 MB')}
            </p>
          </>
        )}
        {loading && <div className="scanline" aria-hidden="true" />}
      </div>

      <div className="upload-actions">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) onFile(file)
            e.target.value = ''
          }}
        />
        <button
          className="btn btn-primary"
          disabled={loading}
          onClick={() => inputRef.current?.click()}
        >
          {loading
            ? t('btn_analyzing', 'Analyzing…')
            : t('btn_analyze', 'Analyze leaf')}
        </button>

        {/* Live camera (getUserMedia); falls back to the native camera input */}
        <input
          ref={cameraFallbackRef}
          type="file"
          accept="image/*"
          capture="environment"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) onFile(file)
            e.target.value = ''
          }}
        />
        <button className="btn btn-ghost" disabled={loading} onClick={openCamera}>
          {t('btn_camera', '📷 Take photo')}
        </button>
      </div>

      {/* Portalled to <body>: .card's entrance animation keeps a transform,
          which would otherwise trap position:fixed inside the card. */}
      {cameraOpen &&
        createPortal(
          <CameraModal onCapture={handleCapture} onClose={() => setCameraOpen(false)} />,
          document.body,
        )}
    </div>
  )
}

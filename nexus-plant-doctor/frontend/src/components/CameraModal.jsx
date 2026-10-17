import { useEffect, useRef, useState } from 'react'
import { useI18n } from '../i18n.jsx'

/**
 * Live camera modal using MediaDevices.getUserMedia.
 * Shows the video feed, grabs a frame on "Capture", and hands the JPEG back.
 * Works on localhost (secure context); degrades with a clear message if the
 * browser blocks or lacks camera access.
 */
export default function CameraModal({ onCapture, onClose }) {
  const { t } = useI18n()
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [error, setError] = useState(null)
  const [starting, setStarting] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError(
          t(
            'cam_no_api',
            'This browser has no camera API — use "Analyze leaf" to pick a file instead.',
          ),
        )
        setStarting(false)
        return
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 } },
          audio: false,
        })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          await videoRef.current.play().catch(() => {})
        }
      } catch (err) {
        if (cancelled) return
        if (err.name === 'NotAllowedError' || err.name === 'SecurityError') {
          setError(
            t(
              'cam_denied',
              'Camera permission denied. Allow camera access in your browser and try again.',
            ),
          )
        } else if (err.name === 'NotFoundError' || err.name === 'OverconstrainedError') {
          setError(
            t('cam_none', 'No camera found on this device — upload a photo instead.'),
          )
        } else {
          setError(
            t('cam_failed', 'Could not open the camera ({err}). Upload a photo instead.', {
              err: err.name,
            }),
          )
        }
      } finally {
        if (!cancelled) setStarting(false)
      }
    }

    start()
    return () => {
      cancelled = true
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const capture = () => {
    const video = videoRef.current
    if (!video || !video.videoWidth) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' }))
      },
      'image/jpeg',
      0.92,
    )
  }

  return (
    <div className="camera-overlay" role="dialog" aria-modal="true" aria-label="Camera capture">
      <div className="camera-box">
        <div className="camera-head">
          <h4>{t('cam_title', '📷 Leaf camera')}</h4>
          <button className="camera-close" onClick={onClose} aria-label={t('cam_cancel', 'Close camera')}>
            ✕
          </button>
        </div>

        <div className="camera-frame">
          {error ? (
            <p className="camera-error">⚠ {error}</p>
          ) : (
            <video ref={videoRef} playsInline muted autoPlay />
          )}
          {starting && !error && (
            <p className="camera-hint">{t('cam_starting', 'Starting camera…')}</p>
          )}
          {!starting && !error && <span className="camera-guide" aria-hidden="true" />}
        </div>

        <div className="camera-actions">
          <button className="btn btn-ghost" onClick={onClose}>
            {t('cam_cancel', 'Cancel')}
          </button>
          <button className="btn btn-primary" onClick={capture} disabled={!!error || starting}>
            {t('cam_capture', '📸 Capture leaf')}
          </button>
        </div>
      </div>
    </div>
  )
}

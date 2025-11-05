import React, { useState, useRef, useEffect } from 'react'

function App() {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [settings, setSettings] = useState({
    silenceThreshold: -40,
    minSilenceDuration: 500,
    padding: 100,
    fps: 30
  })

  const fileInputRef = useRef(null)
  const wsRef = useRef(null)

  // WebSocket connection
  useEffect(() => {
    if (!jobId) return

    // Connect to WebSocket
    const ws = new WebSocket(`ws://localhost:8765/api/ws/${jobId}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'progress':
          setProgress(data.progress)
          setProgressMessage(data.message)
          break

        case 'result':
          setProgress(100)
          setProgressMessage('Complete!')
          setResult(data.result)
          setIsProcessing(false)
          break

        case 'error':
          setError(data.error)
          setIsProcessing(false)
          break

        case 'ping':
          // Respond to ping
          ws.send(JSON.stringify({ type: 'pong' }))
          break

        default:
          break
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setError('WebSocket connection error')
      setIsProcessing(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [jobId])

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.name.endsWith('.mp4') || droppedFile.name.endsWith('.mov'))) {
      setFile(droppedFile)
      setError(null)
      setResult(null)
    } else {
      setError('Please select a valid MP4 or MOV file')
    }
  }

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setResult(null)
    }
  }

  const handleRemoveFile = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setProgress(0)
    setProgressMessage('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleProcess = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    setIsProcessing(true)
    setProgress(0)
    setProgressMessage('Uploading file...')
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('silence_threshold', settings.silenceThreshold)
    formData.append('min_silence_duration', settings.minSilenceDuration)
    formData.append('padding', settings.padding)
    formData.append('fps', settings.fps)

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const data = await response.json()
      setJobId(data.job_id)
      setProgressMessage('File uploaded. Starting analysis...')

    } catch (err) {
      console.error('Upload error:', err)
      setError(err.message || 'Failed to upload file')
      setIsProcessing(false)
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }

  return (
    <div className="container">
      <div className="header">
        <h1>🎬 AutoCut</h1>
        <p>Automatic Silence Detection & Video Cutting</p>
      </div>

      {!file ? (
        <div
          className={`upload-area ${isDragging ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="upload-icon">📁</div>
          <div className="upload-text">Drop your video here or click to browse</div>
          <div className="upload-hint">Supports MP4 and MOV files (up to 10GB)</div>
          <input
            ref={fileInputRef}
            type="file"
            className="file-input"
            accept=".mp4,.mov"
            onChange={handleFileSelect}
          />
        </div>
      ) : (
        <div className="selected-file">
          <div className="file-info">
            <div className="file-icon">🎥</div>
            <div className="file-details">
              <h4>{file.name}</h4>
              <div className="file-size">{formatFileSize(file.size)}</div>
            </div>
          </div>
          {!isProcessing && (
            <button className="remove-btn" onClick={handleRemoveFile}>
              Remove
            </button>
          )}
        </div>
      )}

      {file && !isProcessing && !result && (
        <div className="settings">
          <h3>⚙️ Settings</h3>
          <div className="setting-row">
            <label>Silence Threshold (dB):</label>
            <input
              type="number"
              value={settings.silenceThreshold}
              onChange={(e) => setSettings({ ...settings, silenceThreshold: parseInt(e.target.value) })}
            />
          </div>
          <div className="setting-row">
            <label>Min Silence Duration (ms):</label>
            <input
              type="number"
              value={settings.minSilenceDuration}
              onChange={(e) => setSettings({ ...settings, minSilenceDuration: parseInt(e.target.value) })}
            />
          </div>
          <div className="setting-row">
            <label>Padding (ms):</label>
            <input
              type="number"
              value={settings.padding}
              onChange={(e) => setSettings({ ...settings, padding: parseInt(e.target.value) })}
            />
          </div>
          <div className="setting-row">
            <label>FPS:</label>
            <input
              type="number"
              value={settings.fps}
              onChange={(e) => setSettings({ ...settings, fps: parseInt(e.target.value) })}
            />
          </div>
          <button
            className="process-btn"
            onClick={handleProcess}
            disabled={isProcessing}
          >
            🚀 Process Video
          </button>
        </div>
      )}

      {isProcessing && (
        <div className="progress-container">
          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: `${progress}%` }}>
              {progress.toFixed(0)}%
            </div>
          </div>
          <div className="progress-message">{progressMessage}</div>
        </div>
      )}

      {result && result.success && (
        <div className="results">
          <h3>✅ Processing Complete!</h3>
          <div className="result-item">
            <strong>Video:</strong> {result.video_name}
          </div>
          <div className="result-item">
            <strong>Duration:</strong> {formatTime(result.duration_seconds)}
          </div>
          <div className="result-item">
            <strong>Total Cuts:</strong> {result.total_cuts}
          </div>
          <div className="result-item">
            <strong>Silence Periods Removed:</strong> {result.silence_periods_removed}
          </div>

          <div className="download-section">
            <h4>📥 Download Export Files:</h4>
            {result.exports.premiere_pro && (
              <a
                href={`/api/download/${jobId}/premiere_pro`}
                className="download-btn"
                download
              >
                Premiere Pro XML
              </a>
            )}
            {result.exports.final_cut_pro && (
              <a
                href={`/api/download/${jobId}/final_cut_pro`}
                className="download-btn"
                download
              >
                Final Cut Pro XML
              </a>
            )}
          </div>

          <button
            className="process-btn"
            onClick={handleRemoveFile}
            style={{ marginTop: '20px' }}
          >
            Process Another Video
          </button>
        </div>
      )}

      {error && (
        <div className="error">
          <strong>❌ Error:</strong> {error}
        </div>
      )}
    </div>
  )
}

export default App

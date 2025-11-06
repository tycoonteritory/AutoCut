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
    silenceThreshold: -45,  // Équilibré: détecte les silences sans être trop agressif
    minSilenceDuration: 800,  // 0.8 secondes - bon équilibre
    padding: 250,  // 250ms de marge pour transitions fluides
    fps: 30
  })

  // Phase 2 state
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [transcriptionProgress, setTranscriptionProgress] = useState(0)
  const [transcriptionMessage, setTranscriptionMessage] = useState('')
  const [transcriptionResult, setTranscriptionResult] = useState(null)

  const [isOptimizing, setIsOptimizing] = useState(false)
  const [optimizationProgress, setOptimizationProgress] = useState(0)
  const [optimizationMessage, setOptimizationMessage] = useState('')
  const [optimizationResult, setOptimizationResult] = useState(null)

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
          // Route progress to the active operation
          if (isTranscribing) {
            setTranscriptionProgress(data.progress)
            setTranscriptionMessage(data.message)
          } else if (isOptimizing) {
            setOptimizationProgress(data.progress)
            setOptimizationMessage(data.message)
          } else {
            // Phase 1 processing
            setProgress(data.progress)
            setProgressMessage(data.message)
          }
          break

        case 'result':
          // Handle Phase 2 results
          if (data.result.transcription) {
            setTranscriptionResult(data.result.transcription)
            setIsTranscribing(false)
            setTranscriptionProgress(100)
            setTranscriptionMessage('Transcription complete!')
          } else if (data.result.youtube_optimization) {
            setOptimizationResult(data.result.youtube_optimization)
            setIsOptimizing(false)
            setOptimizationProgress(100)
            setOptimizationMessage('Optimization complete!')
          } else {
            // Phase 1 result
            setProgress(100)
            setProgressMessage('Complete!')
            setResult(data.result)
            setIsProcessing(false)
          }
          break

        case 'error':
          setError(data.error)
          setIsProcessing(false)
          setIsTranscribing(false)
          setIsOptimizing(false)
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
  }, [jobId, isTranscribing, isOptimizing])

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

  const handleTranscribe = async () => {
    if (!jobId) {
      setError('No job ID available')
      return
    }

    setIsTranscribing(true)
    setTranscriptionProgress(0)
    setTranscriptionMessage('Starting transcription...')
    setError(null)

    try {
      const response = await fetch(`/api/transcribe/${jobId}`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Transcription failed: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('Transcription started:', data)

    } catch (err) {
      console.error('Transcription error:', err)
      setError(err.message || 'Failed to start transcription')
      setIsTranscribing(false)
    }
  }

  const handleOptimizeYouTube = async () => {
    if (!jobId) {
      setError('No job ID available')
      return
    }

    if (!transcriptionResult) {
      setError('Please transcribe the video first')
      return
    }

    setIsOptimizing(true)
    setOptimizationProgress(0)
    setOptimizationMessage('Starting YouTube optimization...')
    setError(null)

    try {
      const response = await fetch(`/api/optimize-youtube/${jobId}`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Optimization failed: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('Optimization started:', data)

    } catch (err) {
      console.error('Optimization error:', err)
      setError(err.message || 'Failed to start YouTube optimization')
      setIsOptimizing(false)
    }
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

          {/* Phase 2: Transcription & YouTube Optimization */}
          <div className="phase2-section" style={{ marginTop: '30px', paddingTop: '30px', borderTop: '2px solid #e0e0e0' }}>
            <h3>🎙️ Phase 2: AI Enhancement (Optional)</h3>

            {/* Transcription Section */}
            <div style={{ marginTop: '20px' }}>
              <h4>Transcription</h4>
              {!transcriptionResult && !isTranscribing && (
                <button
                  className="process-btn"
                  onClick={handleTranscribe}
                  disabled={isTranscribing}
                  style={{ backgroundColor: '#4CAF50' }}
                >
                  🎤 Transcrire (Whisper AI)
                </button>
              )}

              {isTranscribing && (
                <div className="progress-container">
                  <div className="progress-bar-container">
                    <div className="progress-bar" style={{ width: `${transcriptionProgress}%` }}>
                      {transcriptionProgress.toFixed(0)}%
                    </div>
                  </div>
                  <div className="progress-message">{transcriptionMessage}</div>
                </div>
              )}

              {transcriptionResult && (
                <div className="results" style={{ marginTop: '15px', backgroundColor: '#f0f9f0' }}>
                  <div className="result-item">
                    <strong>✅ Transcription complete!</strong>
                  </div>
                  <div className="result-item">
                    <strong>Preview:</strong>
                    <div style={{
                      marginTop: '10px',
                      padding: '10px',
                      backgroundColor: '#fff',
                      borderRadius: '5px',
                      maxHeight: '150px',
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap',
                      fontSize: '14px'
                    }}>
                      {transcriptionResult.text || 'No text available'}
                    </div>
                  </div>
                  <div className="download-section">
                    <h4>📥 Download Transcription:</h4>
                    {transcriptionResult.srt_path && (
                      <a
                        href={`/api/download-transcription/${jobId}/srt`}
                        className="download-btn"
                        download
                      >
                        SRT (Subtitles)
                      </a>
                    )}
                    {transcriptionResult.vtt_path && (
                      <a
                        href={`/api/download-transcription/${jobId}/vtt`}
                        className="download-btn"
                        download
                      >
                        VTT (Web Video)
                      </a>
                    )}
                    {transcriptionResult.txt_path && (
                      <a
                        href={`/api/download-transcription/${jobId}/txt`}
                        className="download-btn"
                        download
                      >
                        TXT (Plain Text)
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* YouTube Optimization Section */}
            {transcriptionResult && (
              <div style={{ marginTop: '30px' }}>
                <h4>YouTube Optimization</h4>
                {!optimizationResult && !isOptimizing && (
                  <button
                    className="process-btn"
                    onClick={handleOptimizeYouTube}
                    disabled={isOptimizing}
                    style={{ backgroundColor: '#FF0000' }}
                  >
                    🎬 Optimiser pour YouTube (GPT-4)
                  </button>
                )}

                {isOptimizing && (
                  <div className="progress-container">
                    <div className="progress-bar-container">
                      <div className="progress-bar" style={{ width: `${optimizationProgress}%` }}>
                        {optimizationProgress.toFixed(0)}%
                      </div>
                    </div>
                    <div className="progress-message">{optimizationMessage}</div>
                  </div>
                )}

                {optimizationResult && (
                  <div className="results" style={{ marginTop: '15px', backgroundColor: '#fff5f5' }}>
                    <div className="result-item">
                      <strong>✅ YouTube optimization complete!</strong>
                    </div>

                    {/* Titles */}
                    {optimizationResult.titles && optimizationResult.titles.length > 0 && (
                      <div style={{ marginTop: '15px' }}>
                        <strong>📝 Suggested Titles:</strong>
                        <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
                          {optimizationResult.titles.map((title, idx) => (
                            <li key={idx}>{title}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Thumbnails */}
                    {optimizationResult.thumbnails && optimizationResult.thumbnails.length > 0 && (
                      <div style={{ marginTop: '15px' }}>
                        <strong>🖼️ Suggested Thumbnails:</strong>
                        <div style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
                          {optimizationResult.thumbnails.map((thumb, idx) => (
                            <div key={idx} style={{ textAlign: 'center' }}>
                              <img
                                src={thumb.url}
                                alt={`Thumbnail ${idx + 1}`}
                                style={{ width: '200px', height: 'auto', borderRadius: '8px', border: '2px solid #ddd' }}
                              />
                              <div style={{ fontSize: '12px', marginTop: '5px' }}>
                                @ {formatTime(thumb.timestamp)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Tags */}
                    {optimizationResult.tags && optimizationResult.tags.length > 0 && (
                      <div style={{ marginTop: '15px' }}>
                        <strong>🏷️ Tags:</strong>
                        <div style={{ marginTop: '10px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {optimizationResult.tags.map((tag, idx) => (
                            <span key={idx} style={{
                              backgroundColor: '#e0e0e0',
                              padding: '5px 10px',
                              borderRadius: '5px',
                              fontSize: '14px'
                            }}>
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Description */}
                    {optimizationResult.description && (
                      <div style={{ marginTop: '15px' }}>
                        <strong>📄 Description:</strong>
                        <pre style={{
                          marginTop: '10px',
                          padding: '15px',
                          backgroundColor: '#f5f5f5',
                          borderRadius: '8px',
                          whiteSpace: 'pre-wrap',
                          fontSize: '14px'
                        }}>
                          {optimizationResult.description}
                        </pre>
                      </div>
                    )}

                    {/* Chapters */}
                    {optimizationResult.chapters && optimizationResult.chapters.length > 0 && (
                      <div style={{ marginTop: '15px' }}>
                        <strong>📑 Chapters:</strong>
                        <div style={{ marginTop: '10px' }}>
                          {optimizationResult.chapters.map((chapter, idx) => (
                            <div key={idx} style={{ marginBottom: '8px' }}>
                              <code>{chapter.timestamp}</code> - {chapter.title}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <button
            className="process-btn"
            onClick={handleRemoveFile}
            style={{ marginTop: '30px' }}
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

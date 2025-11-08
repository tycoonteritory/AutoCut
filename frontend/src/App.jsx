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
  const [presetLevel, setPresetLevel] = useState(3) // 1-5, défaut = 3 (Normal)
  const [advancedMode, setAdvancedMode] = useState(false)
  const [settings, setSettings] = useState({
    silenceThreshold: -45,  // Équilibré: détecte les silences sans être trop agressif
    minSilenceDuration: 800,  // 0.8 secondes - bon équilibre
    padding: 250,  // 250ms de marge pour transitions fluides
    fps: 30,
    detectFillerWords: false,  // Détection des hésitations (euh, hum, etc.)
    fillerSensitivity: 0.7,  // Sensibilité (0.0-1.0)
    whisperModel: 'base',  // Modèle Whisper pour la transcription
    enableAudioEnhancement: false,  // Débruitage audio
    noiseReductionStrength: 0.7  // Force du débruitage (0.0-1.0)
  })

  // Preset configurations
  const presets = {
    1: { // Très conservateur - Peu de coupes
      silenceThreshold: -50,
      minSilenceDuration: 1500,
      padding: 400,
      label: 'Très Conservateur',
      description: 'Garde presque toutes les pauses naturelles'
    },
    2: { // Conservateur
      silenceThreshold: -47,
      minSilenceDuration: 1100,
      padding: 325,
      label: 'Conservateur',
      description: 'Coupe les longs silences uniquement'
    },
    3: { // Normal (défaut actuel)
      silenceThreshold: -45,
      minSilenceDuration: 800,
      padding: 250,
      label: 'Normal',
      description: 'Bon équilibre entre fluidité et efficacité'
    },
    4: { // Agressif
      silenceThreshold: -42,
      minSilenceDuration: 600,
      padding: 150,
      label: 'Agressif',
      description: 'Coupe davantage de pauses et silences'
    },
    5: { // Très agressif - Beaucoup de coupes
      silenceThreshold: -38,
      minSilenceDuration: 400,
      padding: 100,
      label: 'Très Agressif',
      description: 'Tempo rapide, coupe un maximum'
    }
  }

  // Update settings when preset level changes
  const handlePresetChange = (level) => {
    setPresetLevel(level)
    const preset = presets[level]
    setSettings({
      ...settings,
      silenceThreshold: preset.silenceThreshold,
      minSilenceDuration: preset.minSilenceDuration,
      padding: preset.padding
    })
  }

  // Phase 2 state
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [transcriptionProgress, setTranscriptionProgress] = useState(0)
  const [transcriptionMessage, setTranscriptionMessage] = useState('')
  const [transcriptionResult, setTranscriptionResult] = useState(null)

  const [isOptimizing, setIsOptimizing] = useState(false)
  const [optimizationProgress, setOptimizationProgress] = useState(0)
  const [optimizationMessage, setOptimizationMessage] = useState('')
  const [optimizationResult, setOptimizationResult] = useState(null)

  const [isGeneratingClips, setIsGeneratingClips] = useState(false)
  const [clipsProgress, setClipsProgress] = useState(0)
  const [clipsMessage, setClipsMessage] = useState('')
  const [clipsResult, setClipsResult] = useState(null)
  const [numClips, setNumClips] = useState(3)
  const [clipFormat, setClipFormat] = useState('horizontal')

  // History state
  const [showHistory, setShowHistory] = useState(false)
  const [jobHistory, setJobHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)

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
          } else if (isGeneratingClips) {
            setClipsProgress(data.progress)
            setClipsMessage(data.message)
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
          } else if (data.result.short_clips) {
            setClipsResult(data.result.short_clips)
            setIsGeneratingClips(false)
            setClipsProgress(100)
            setClipsMessage('Clips générés avec succès!')
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
          setIsGeneratingClips(false)
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
  }, [jobId, isTranscribing, isOptimizing, isGeneratingClips])

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
    formData.append('detect_filler_words', settings.detectFillerWords)
    formData.append('filler_sensitivity', settings.fillerSensitivity)
    formData.append('whisper_model', settings.whisperModel)
    formData.append('enable_audio_enhancement', settings.enableAudioEnhancement)
    formData.append('noise_reduction_strength', settings.noiseReductionStrength)

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

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const response = await fetch('/api/history?limit=50')
      if (!response.ok) {
        throw new Error('Failed to load history')
      }
      const data = await response.json()
      setJobHistory(data.jobs)
    } catch (err) {
      console.error('Error loading history:', err)
      setError('Failed to load job history')
    } finally {
      setHistoryLoading(false)
    }
  }

  const deleteHistoryJob = async (historyJobId) => {
    try {
      const response = await fetch(`/api/job/${historyJobId}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error('Failed to delete job')
      }
      // Reload history after deletion
      loadHistory()
    } catch (err) {
      console.error('Error deleting job:', err)
      setError('Failed to delete job')
    }
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

  const handleGenerateClips = async () => {
    if (!jobId) {
      setError('No job ID available')
      return
    }

    if (!transcriptionResult) {
      setError('Please transcribe the video first')
      return
    }

    setIsGeneratingClips(true)
    setClipsProgress(0)
    setClipsMessage('Starting short clips generation...')
    setError(null)

    try {
      const response = await fetch(`/api/generate-clips/${jobId}?num_clips=${numClips}&clip_format=${clipFormat}`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Clips generation failed: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('Clips generation started:', data)

    } catch (err) {
      console.error('Clips generation error:', err)
      setError(err.message || 'Failed to start clips generation')
      setIsGeneratingClips(false)
    }
  }

  return (
    <div className="container">
      <div className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>🎬 AutoCut</h1>
          <p>Automatic Silence Detection & Video Cutting</p>
        </div>
        <button
          onClick={() => {
            setShowHistory(!showHistory)
            if (!showHistory) loadHistory()
          }}
          style={{
            padding: '10px 20px',
            backgroundColor: showHistory ? '#0ea5e9' : '#2a2a2a',
            color: '#fff',
            border: showHistory ? '2px solid #0ea5e9' : '2px solid #3a3a3a',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 'bold',
            transition: 'all 0.2s'
          }}
        >
          {showHistory ? '🏠 Nouveau Job' : '📜 Historique'}
        </button>
      </div>

      {showHistory ? (
        /* History View */
        <div style={{ marginTop: '20px' }}>
          <h2 style={{ color: '#0ea5e9', marginBottom: '20px' }}>📜 Historique des Traitements</h2>

          {historyLoading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
              Chargement de l'historique...
            </div>
          ) : jobHistory.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
              Aucun traitement dans l'historique
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gap: '15px'
            }}>
              {jobHistory.map((histJob) => (
                <div
                  key={histJob.id}
                  style={{
                    padding: '20px',
                    backgroundColor: '#222',
                    borderRadius: '10px',
                    border: '1px solid #3a3a3a'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '10px'
                  }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: '0 0 5px 0', color: '#fff' }}>{histJob.filename}</h3>
                      <div style={{ fontSize: '12px', color: '#888' }}>
                        {new Date(histJob.created_at).toLocaleString('fr-FR')}
                      </div>
                    </div>
                    <div style={{
                      padding: '5px 12px',
                      borderRadius: '5px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      backgroundColor: histJob.status === 'completed' ? '#22c55e' : histJob.status === 'failed' ? '#ef4444' : '#fbbf24',
                      color: '#000'
                    }}>
                      {histJob.status === 'completed' ? '✅ Terminé' : histJob.status === 'failed' ? '❌ Échoué' : '⏳ En cours'}
                    </div>
                  </div>

                  {histJob.status === 'completed' && histJob.result && (
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                      gap: '10px',
                      marginTop: '15px',
                      padding: '15px',
                      backgroundColor: '#1a1a1a',
                      borderRadius: '8px'
                    }}>
                      <div>
                        <div style={{ fontSize: '11px', color: '#888' }}>⏱️ Durée finale</div>
                        <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#4ade80' }}>
                          {formatTime(histJob.duration_seconds || 0)}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: '#888' }}>✂️ Coupes</div>
                        <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#5b9aff' }}>
                          {histJob.total_cuts}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: '#888' }}>⚡ Temps gagné</div>
                        <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#a78bfa' }}>
                          {histJob.percentage_saved?.toFixed(1)}%
                        </div>
                      </div>
                      {histJob.filler_words_detected > 0 && (
                        <div>
                          <div style={{ fontSize: '11px', color: '#888' }}>🎤 Hésitations</div>
                          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fbbf24' }}>
                            {histJob.filler_words_detected}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {histJob.status === 'completed' && (
                    <div style={{
                      marginTop: '15px',
                      display: 'flex',
                      gap: '10px'
                    }}>
                      {histJob.premiere_pro_export && (
                        <a
                          href={`/api/download/${histJob.id}/premiere_pro`}
                          download
                          style={{
                            padding: '8px 16px',
                            backgroundColor: '#0ea5e9',
                            color: '#fff',
                            borderRadius: '6px',
                            textDecoration: 'none',
                            fontSize: '13px',
                            fontWeight: 'bold'
                          }}
                        >
                          📥 Premiere Pro
                        </a>
                      )}
                      {histJob.final_cut_pro_export && (
                        <a
                          href={`/api/download/${histJob.id}/final_cut_pro`}
                          download
                          style={{
                            padding: '8px 16px',
                            backgroundColor: '#0ea5e9',
                            color: '#fff',
                            borderRadius: '6px',
                            textDecoration: 'none',
                            fontSize: '13px',
                            fontWeight: 'bold'
                          }}
                        >
                          📥 Final Cut Pro
                        </a>
                      )}
                      <button
                        onClick={() => deleteHistoryJob(histJob.id)}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#ef4444',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '13px',
                          fontWeight: 'bold',
                          marginLeft: 'auto'
                        }}
                      >
                        🗑️ Supprimer
                      </button>
                    </div>
                  )}

                  {histJob.status === 'failed' && histJob.error && (
                    <div style={{
                      marginTop: '10px',
                      padding: '10px',
                      backgroundColor: '#3a1a1a',
                      borderRadius: '6px',
                      color: '#ef4444',
                      fontSize: '13px'
                    }}>
                      ⚠️ Erreur: {histJob.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Main Processing View */
        <>
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
          <h3>⚙️ Niveau de Coupe</h3>

          {/* Preset Slider */}
          <div style={{ marginBottom: '30px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '10px',
              fontSize: '13px',
              color: '#666'
            }}>
              <span>⬅️ Moins de coupes</span>
              <span style={{ fontWeight: 'bold', color: '#0ea5e9' }}>
                {presets[presetLevel].label}
              </span>
              <span>Plus de coupes ➡️</span>
            </div>

            <input
              type="range"
              min="1"
              max="5"
              value={presetLevel}
              onChange={(e) => handlePresetChange(parseInt(e.target.value))}
              style={{
                width: '100%',
                height: '8px',
                borderRadius: '4px',
                background: `linear-gradient(to right, #22c55e 0%, #0ea5e9 50%, #ef4444 100%)`,
                outline: 'none',
                cursor: 'pointer'
              }}
            />

            {/* Level markers */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: '5px',
              fontSize: '11px',
              color: '#999'
            }}>
              <span>1</span>
              <span>2</span>
              <span>3</span>
              <span>4</span>
              <span>5</span>
            </div>

            {/* Description */}
            <div style={{
              marginTop: '15px',
              padding: '12px',
              backgroundColor: '#2a2a2a',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#aaa',
              textAlign: 'center',
              border: '1px solid #3a3a3a'
            }}>
              💡 {presets[presetLevel].description}
            </div>
          </div>

          {/* Filler Words Detection Section */}
          <div style={{
            marginBottom: '25px',
            padding: '18px',
            backgroundColor: '#1e293b',
            borderRadius: '10px',
            border: '2px solid #334155'
          }}>
            <h3 style={{
              marginTop: 0,
              marginBottom: '15px',
              fontSize: '16px',
              color: '#0ea5e9',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              🎤 Détection d'Hésitations
            </h3>

            <div style={{ marginBottom: '15px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                cursor: 'pointer',
                fontSize: '14px',
                color: '#e2e8f0'
              }}>
                <input
                  type="checkbox"
                  checked={settings.detectFillerWords}
                  onChange={(e) => setSettings({ ...settings, detectFillerWords: e.target.checked })}
                  style={{
                    width: '20px',
                    height: '20px',
                    cursor: 'pointer'
                  }}
                />
                <span>Supprimer les "euh", "hum", "ben", etc.</span>
              </label>
            </div>

            {settings.detectFillerWords && (
              <div style={{
                marginTop: '15px',
                paddingTop: '15px',
                borderTop: '1px solid #334155'
              }}>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '8px',
                    fontSize: '13px',
                    color: '#94a3b8'
                  }}>
                    Sensibilité de détection:
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={settings.fillerSensitivity}
                    onChange={(e) => setSettings({ ...settings, fillerSensitivity: parseFloat(e.target.value) })}
                    style={{
                      width: '100%',
                      height: '6px',
                      borderRadius: '3px',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  />
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginTop: '5px',
                    fontSize: '11px',
                    color: '#64748b'
                  }}>
                    <span>Précis</span>
                    <span style={{ fontWeight: 'bold', color: '#0ea5e9' }}>
                      {(settings.fillerSensitivity * 100).toFixed(0)}%
                    </span>
                    <span>Agressif</span>
                  </div>
                </div>

                <div style={{
                  padding: '10px',
                  backgroundColor: '#0f172a',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: '#94a3b8',
                  lineHeight: '1.5'
                }}>
                  💡 <strong style={{ color: '#0ea5e9' }}>Cette fonctionnalité détecte :</strong>
                  <br />
                  • Les hésitations vocales (euh, heu, euuh)
                  <br />
                  • Les sons d'hésitation (hum, hmm)
                  <br />
                  • Les mots de remplissage (ben, bah, alors euh, donc euh)
                  <br />
                  <br />
                  ⚠️ <em>Nécessite ~30 secondes de traitement supplémentaire</em>
                </div>
              </div>
            )}
          </div>

          {/* Advanced mode toggle */}
          <div style={{ textAlign: 'center', marginBottom: '15px' }}>
            <button
              onClick={() => setAdvancedMode(!advancedMode)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#0ea5e9',
                fontSize: '13px',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              {advancedMode ? '🔼 Masquer paramètres avancés' : '🔽 Afficher paramètres avancés'}
            </button>
          </div>

          {/* Advanced settings - hidden by default */}
          {advancedMode && (
            <div style={{
              marginTop: '20px',
              padding: '15px',
              backgroundColor: '#2a2520',
              borderRadius: '8px',
              border: '1px solid #5a4520'
            }}>
              <h4 style={{ marginTop: 0, fontSize: '14px', color: '#fbbf24' }}>
                ⚙️ Paramètres Avancés
              </h4>
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

              {/* Audio Enhancement Section */}
              <div style={{
                marginTop: '20px',
                paddingTop: '15px',
                borderTop: '1px solid #5a4520'
              }}>
                <h4 style={{ marginTop: 0, fontSize: '14px', color: '#fbbf24' }}>
                  🔊 Amélioration Audio (Expérimental)
                </h4>
                <div style={{ marginBottom: '15px' }}>
                  <label style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    color: '#e2e8f0'
                  }}>
                    <input
                      type="checkbox"
                      checked={settings.enableAudioEnhancement}
                      onChange={(e) => setSettings({ ...settings, enableAudioEnhancement: e.target.checked })}
                      style={{
                        width: '16px',
                        height: '16px',
                        cursor: 'pointer'
                      }}
                    />
                    <span>Activer le débruitage audio</span>
                  </label>
                </div>

                {settings.enableAudioEnhancement && (
                  <div style={{ marginTop: '10px' }}>
                    <label style={{
                      display: 'block',
                      marginBottom: '8px',
                      fontSize: '12px',
                      color: '#94a3b8'
                    }}>
                      Intensité du débruitage:
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={settings.noiseReductionStrength}
                      onChange={(e) => setSettings({ ...settings, noiseReductionStrength: parseFloat(e.target.value) })}
                      style={{
                        width: '100%',
                        height: '4px',
                        borderRadius: '2px',
                        outline: 'none',
                        cursor: 'pointer'
                      }}
                    />
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginTop: '5px',
                      fontSize: '10px',
                      color: '#64748b'
                    }}>
                      <span>Léger</span>
                      <span style={{ fontWeight: 'bold', color: '#fbbf24' }}>
                        {(settings.noiseReductionStrength * 100).toFixed(0)}%
                      </span>
                      <span>Fort</span>
                    </div>
                    <div style={{
                      marginTop: '10px',
                      padding: '8px',
                      backgroundColor: '#1a1510',
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: '#94a3b8',
                      lineHeight: '1.4'
                    }}>
                      ⚠️ Le débruitage améliore la détection mais ajoute ~10s de traitement
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

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

          {/* Statistics Section */}
          <div style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#1a2530',
            borderRadius: '8px',
            border: '1px solid #2a3a4a'
          }}>
            <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#5b9aff' }}>📊 Statistics</h4>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div style={{ padding: '10px', backgroundColor: '#222', borderRadius: '6px', border: '1px solid #2a2a2a' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>⏱️ Original Duration</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#e0e0e0' }}>
                  {formatTime(result.duration_seconds)}
                </div>
              </div>

              <div style={{ padding: '10px', backgroundColor: '#222', borderRadius: '6px', border: '1px solid #2a2a2a' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>✂️ Final Duration</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#4ade80' }}>
                  {formatTime(result.kept_duration_seconds)}
                </div>
              </div>

              <div style={{ padding: '10px', backgroundColor: '#222', borderRadius: '6px', border: '1px solid #2a2a2a' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>🎬 Number of Cuts</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#5b9aff' }}>
                  {result.total_cuts}
                </div>
              </div>

              <div style={{ padding: '10px', backgroundColor: '#222', borderRadius: '6px', border: '1px solid #2a2a2a' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>🔇 Silences Removed</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ef4444' }}>
                  {result.silence_periods_removed}
                </div>
              </div>

              {result.filler_words_detected !== undefined && result.filler_words_detected > 0 && (
                <div style={{ padding: '10px', backgroundColor: '#222', borderRadius: '6px', border: '1px solid #2a2a2a' }}>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>🎤 Hésitations Removed</div>
                  <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#fbbf24' }}>
                    {result.filler_words_detected}
                  </div>
                </div>
              )}

              <div style={{ padding: '10px', backgroundColor: '#222', borderRadius: '6px', border: '1px solid #2a2a2a', gridColumn: '1 / -1' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>⚡ Time Saved</div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
                  <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#a78bfa' }}>
                    {formatTime(result.removed_duration_seconds)}
                  </span>
                  <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#a78bfa' }}>
                    ({result.percentage_saved}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="download-section" style={{ marginTop: '20px' }}>
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
                <div className="results" style={{ marginTop: '15px', backgroundColor: '#1a2a1a' }}>
                  <div className="result-item">
                    <strong>✅ Transcription complete!</strong>
                  </div>
                  <div className="result-item">
                    <strong>Preview:</strong>
                    <div style={{
                      marginTop: '10px',
                      padding: '10px',
                      backgroundColor: '#2a2a2a',
                      borderRadius: '5px',
                      maxHeight: '150px',
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap',
                      fontSize: '14px',
                      color: '#e0e0e0',
                      border: '1px solid #3a3a3a'
                    }}>
                      {transcriptionResult.text || 'No text available'}
                    </div>
                  </div>
                  <div className="download-section">
                    <h4>📥 Télécharger la Transcription :</h4>
                    {transcriptionResult.srt_path && (
                      <a
                        href={`/api/download-transcription/${jobId}/srt`}
                        className="download-btn"
                        download
                        title="Format sous-titres avec timecodes"
                      >
                        📄 SRT (avec timecodes)
                      </a>
                    )}
                    {transcriptionResult.vtt_path && (
                      <a
                        href={`/api/download-transcription/${jobId}/vtt`}
                        className="download-btn"
                        download
                        title="Format web video avec timecodes"
                      >
                        📄 VTT (avec timecodes)
                      </a>
                    )}
                    {transcriptionResult.txt_path && (
                      <a
                        href={`/api/download-transcription/${jobId}/txt`}
                        className="download-btn"
                        download
                        title="Texte brut sans timecodes - Idéal pour réutiliser sans coût de transcription"
                        style={{ backgroundColor: '#22c55e' }}
                      >
                        📝 TXT (SANS timecodes) 💰
                      </a>
                    )}
                  </div>
                  <div style={{
                    marginTop: '10px',
                    padding: '12px',
                    backgroundColor: '#1a2a1a',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#4ade80',
                    border: '1px solid #2a4a2a'
                  }}>
                    💡 <strong>Astuce :</strong> Le fichier TXT contient uniquement le texte sans timecodes. Parfait pour réutiliser la transcription avec d'autres outils AI sans avoir à payer OpenAI à nouveau !
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
                  <div className="results" style={{ marginTop: '15px', backgroundColor: '#2a1a1a' }}>
                    <div className="result-item">
                      <strong>✅ YouTube optimization complete!</strong>
                    </div>

                    {/* Titles */}
                    {optimizationResult.titles && optimizationResult.titles.length > 0 && (
                      <div style={{ marginTop: '15px' }}>
                        <strong>📝 Suggestions de Titres YouTube :</strong>
                        <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {optimizationResult.titles.map((title, idx) => (
                            <div key={idx} style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              padding: '12px',
                              backgroundColor: '#2a2a2a',
                              borderRadius: '6px',
                              border: '1px solid #3a3a3a'
                            }}>
                              <span style={{ fontSize: '14px', color: '#e0e0e0', flex: 1 }}>
                                <strong style={{ color: '#0ea5e9' }}>#{idx + 1}</strong> {title}
                              </span>
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(title);
                                  alert(`Titre #${idx + 1} copié ! 📋`);
                                }}
                                style={{
                                  padding: '6px 12px',
                                  backgroundColor: '#0ea5e9',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px',
                                  fontWeight: 'bold',
                                  marginLeft: '10px'
                                }}
                              >
                                📋 Copier
                              </button>
                            </div>
                          ))}
                        </div>
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
                                style={{ width: '200px', height: 'auto', borderRadius: '8px', border: '1px solid #3a3a3a' }}
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
                              backgroundColor: '#2a2a2a',
                              color: '#5b9aff',
                              padding: '5px 10px',
                              borderRadius: '5px',
                              fontSize: '14px',
                              border: '1px solid #3a3a3a'
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                          <strong>📄 Description YouTube :</strong>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(optimizationResult.description);
                              alert('Description copiée dans le presse-papiers ! 📋');
                            }}
                            style={{
                              padding: '8px 16px',
                              backgroundColor: '#0ea5e9',
                              color: '#fff',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '13px',
                              fontWeight: 'bold'
                            }}
                          >
                            📋 Copier
                          </button>
                        </div>
                        <pre style={{
                          marginTop: '10px',
                          padding: '15px',
                          backgroundColor: '#2a2a2a',
                          borderRadius: '8px',
                          whiteSpace: 'pre-wrap',
                          fontSize: '14px',
                          color: '#e0e0e0',
                          border: '1px solid #3a3a3a',
                          maxHeight: '200px',
                          overflowY: 'auto'
                        }}>
                          {optimizationResult.description}
                        </pre>
                      </div>
                    )}

                    {/* Chapters */}
                    {optimizationResult.chapters && optimizationResult.chapters.length > 0 && (
                      <div style={{ marginTop: '15px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                          <strong>📑 Chapitres YouTube (à copier dans la description) :</strong>
                          <button
                            onClick={() => {
                              const chaptersText = optimizationResult.chapters
                                .map(chapter => `${chapter.time} ${chapter.title}`)
                                .join('\n');
                              navigator.clipboard.writeText(chaptersText);
                              alert('Chapitres copiés dans le presse-papiers ! 📋');
                            }}
                            style={{
                              padding: '8px 16px',
                              backgroundColor: '#0ea5e9',
                              color: '#fff',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '13px',
                              fontWeight: 'bold'
                            }}
                          >
                            📋 Copier pour YouTube
                          </button>
                        </div>
                        <div style={{
                          marginTop: '10px',
                          padding: '15px',
                          backgroundColor: '#2a2a2a',
                          borderRadius: '8px',
                          fontFamily: 'monospace',
                          fontSize: '14px',
                          maxHeight: '300px',
                          overflowY: 'auto',
                          border: '1px solid #3a3a3a'
                        }}>
                          {optimizationResult.chapters.map((chapter, idx) => (
                            <div key={idx} style={{ marginBottom: '8px', color: '#e0e0e0' }}>
                              <span style={{ color: '#0ea5e9', fontWeight: 'bold' }}>{chapter.time}</span> {chapter.title}
                            </div>
                          ))}
                        </div>
                        <div style={{
                          marginTop: '8px',
                          padding: '10px',
                          backgroundColor: '#1a2a1a',
                          borderRadius: '6px',
                          fontSize: '12px',
                          color: '#4ade80',
                          border: '1px solid #2a4a2a'
                        }}>
                          💡 Astuce : Collez ce chapitrage directement dans votre description YouTube pour améliorer la navigation de vos viewers !
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Short Clips Generation Section */}
            {transcriptionResult && (
              <div style={{ marginTop: '30px', paddingTop: '30px', borderTop: '2px solid #e0e0e0' }}>
                <h4>✂️ Clips Courts (TikTok/Reels/Shorts)</h4>
                <p style={{ fontSize: '14px', color: '#888', marginBottom: '15px' }}>
                  Génère automatiquement les meilleurs moments de votre vidéo pour les réseaux sociaux
                </p>

                {!clipsResult && !isGeneratingClips && (
                  <div>
                    {/* Configuration */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '15px',
                      marginBottom: '20px',
                      padding: '15px',
                      backgroundColor: '#1a2530',
                      borderRadius: '8px',
                      border: '1px solid #2a3a4a'
                    }}>
                      <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: '#888' }}>
                          Nombre de clips :
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="10"
                          value={numClips}
                          onChange={(e) => setNumClips(parseInt(e.target.value))}
                          style={{
                            width: '100%',
                            padding: '10px',
                            backgroundColor: '#222',
                            border: '1px solid #3a3a3a',
                            borderRadius: '6px',
                            color: '#fff',
                            fontSize: '14px'
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: '#888' }}>
                          Format :
                        </label>
                        <select
                          value={clipFormat}
                          onChange={(e) => setClipFormat(e.target.value)}
                          style={{
                            width: '100%',
                            padding: '10px',
                            backgroundColor: '#222',
                            border: '1px solid #3a3a3a',
                            borderRadius: '6px',
                            color: '#fff',
                            fontSize: '14px',
                            cursor: 'pointer'
                          }}
                        >
                          <option value="horizontal">📺 Horizontal (16:9 - YouTube)</option>
                          <option value="vertical">📱 Vertical (9:16 - TikTok/Reels)</option>
                        </select>
                      </div>
                    </div>

                    <button
                      className="process-btn"
                      onClick={handleGenerateClips}
                      disabled={isGeneratingClips}
                      style={{ backgroundColor: '#10b981' }}
                    >
                      ✂️ Générer les Clips Courts
                    </button>
                  </div>
                )}

                {isGeneratingClips && (
                  <div className="progress-container">
                    <div className="progress-bar-container">
                      <div className="progress-bar" style={{ width: `${clipsProgress}%` }}>
                        {clipsProgress.toFixed(0)}%
                      </div>
                    </div>
                    <div className="progress-message">{clipsMessage}</div>
                  </div>
                )}

                {clipsResult && clipsResult.success && (
                  <div className="results" style={{ marginTop: '15px', backgroundColor: '#1a2a1a' }}>
                    <div className="result-item">
                      <strong>✅ {clipsResult.num_clips} clips générés avec succès !</strong>
                    </div>

                    <div style={{ marginTop: '20px', display: 'grid', gap: '20px' }}>
                      {clipsResult.clips.map((clip, idx) => (
                        <div key={idx} style={{
                          padding: '20px',
                          backgroundColor: '#2a2a2a',
                          borderRadius: '10px',
                          border: '1px solid #3a3a3a'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                            <div style={{ flex: 1 }}>
                              <h4 style={{ margin: '0 0 8px 0', color: '#10b981' }}>
                                🎬 Clip #{idx + 1}: {clip.title}
                              </h4>
                              <div style={{ fontSize: '13px', color: '#888', marginBottom: '8px' }}>
                                ⏱️ Durée: {Math.floor(clip.duration)}s |
                                🕐 {Math.floor(clip.start_time / 60)}:{Math.floor(clip.start_time % 60).toString().padStart(2, '0')} → {Math.floor(clip.end_time / 60)}:{Math.floor(clip.end_time % 60).toString().padStart(2, '0')}
                              </div>
                              {clip.hook && (
                                <div style={{
                                  padding: '10px',
                                  backgroundColor: '#1a1a1a',
                                  borderRadius: '6px',
                                  fontSize: '13px',
                                  color: '#fbbf24',
                                  marginTop: '8px'
                                }}>
                                  🎯 Hook: "{clip.hook}"
                                </div>
                              )}
                              {clip.why_interesting && (
                                <div style={{
                                  padding: '10px',
                                  backgroundColor: '#1a1a1a',
                                  borderRadius: '6px',
                                  fontSize: '12px',
                                  color: '#888',
                                  marginTop: '8px'
                                }}>
                                  💡 {clip.why_interesting}
                                </div>
                              )}
                            </div>
                          </div>

                          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
                            <a
                              href={`/api/download-clip/${jobId}/${idx}`}
                              download
                              style={{
                                padding: '10px 20px',
                                backgroundColor: '#10b981',
                                color: '#fff',
                                borderRadius: '6px',
                                textDecoration: 'none',
                                fontSize: '14px',
                                fontWeight: 'bold',
                                display: 'inline-block'
                              }}
                            >
                              📥 Télécharger
                            </a>
                            {clip.url && (
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(clip.title);
                                  alert('Titre copié ! 📋');
                                }}
                                style={{
                                  padding: '10px 20px',
                                  backgroundColor: '#0ea5e9',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: '6px',
                                  cursor: 'pointer',
                                  fontSize: '14px',
                                  fontWeight: 'bold'
                                }}
                              >
                                📋 Copier le titre
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div style={{
                      marginTop: '20px',
                      padding: '15px',
                      backgroundColor: '#1a2a1a',
                      borderRadius: '8px',
                      fontSize: '13px',
                      color: '#4ade80',
                      border: '1px solid #2a4a2a'
                    }}>
                      🎯 <strong>Astuce :</strong> Les clips sont analysés par GPT-4 pour identifier les moments les plus viraux et engageants. Format: {clipsResult.format === 'vertical' ? '9:16 (TikTok/Reels)' : '16:9 (YouTube Shorts)'}
                    </div>
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
      </>
      )}
    </div>
  )
}

export default App

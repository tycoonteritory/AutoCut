import React, { useState, useRef, useEffect } from 'react'

// Utility function to handle fetch errors
const getFetchErrorMessage = (err) => {
  if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
    return '❌ Impossible de se connecter au serveur backend. Vérifiez que le serveur est démarré sur le port 8765.'
  }
  return err.message || 'Une erreur est survenue'
}

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
    silenceThreshold: -45,
    minSilenceDuration: 800,
    padding: 250,
    fps: 30,
    detectFillerWords: true,  // Activé par défaut maintenant
    fillerSensitivity: 0.7,
    whisperModel: 'base',
    enableAudioEnhancement: false,
    noiseReductionStrength: 0.7
  })

  // Title generation state
  const [isGeneratingTitles, setIsGeneratingTitles] = useState(false)
  const [generatedTitles, setGeneratedTitles] = useState(null)
  const [copiedTitleIndex, setCopiedTitleIndex] = useState(null)

  // Preset configurations
  const presets = {
    1: {
      silenceThreshold: -50,
      minSilenceDuration: 1500,
      padding: 400,
      label: 'Très Conservateur',
      description: 'Garde presque toutes les pauses naturelles'
    },
    2: {
      silenceThreshold: -47,
      minSilenceDuration: 1100,
      padding: 325,
      label: 'Conservateur',
      description: 'Coupe les longs silences uniquement'
    },
    3: {
      silenceThreshold: -45,
      minSilenceDuration: 800,
      padding: 250,
      label: 'Normal',
      description: 'Bon équilibre entre fluidité et efficacité'
    },
    4: {
      silenceThreshold: -42,
      minSilenceDuration: 600,
      padding: 150,
      label: 'Agressif',
      description: 'Coupe davantage de pauses et silences'
    },
    5: {
      silenceThreshold: -38,
      minSilenceDuration: 400,
      padding: 100,
      label: 'Très Agressif',
      description: 'Tempo rapide, coupe un maximum'
    }
  }

  const fileInputRef = useRef(null)
  const wsRef = useRef(null)

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

  // WebSocket connection
  useEffect(() => {
    if (!jobId) return

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
          setProgressMessage('Traitement terminé !')
          setResult(data.result)
          setIsProcessing(false)
          break

        case 'error':
          setError(data.error)
          setIsProcessing(false)
          break

        case 'ping':
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
      setError('Veuillez sélectionner un fichier MP4 ou MOV valide')
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
    setGeneratedTitles(null)
    setJobId(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleProcess = async () => {
    if (!file) {
      setError('Veuillez d\'abord sélectionner un fichier')
      return
    }

    setIsProcessing(true)
    setProgress(0)
    setProgressMessage('Envoi du fichier...')
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
    formData.append('processing_mode', 'local') // Toujours en mode local

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        let errorMessage = `Upload failed: ${response.statusText}`
        try {
          const errorData = await response.json()
          if (errorData.detail) {
            errorMessage = errorData.detail
          }
        } catch (e) {
          if (response.status === 500) {
            errorMessage = '❌ Erreur serveur lors de l\'upload. Vérifiez les logs du backend ou redémarrez le serveur.'
          }
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setJobId(data.job_id)
      setProgressMessage('Fichier envoyé. Démarrage de l\'analyse...')

    } catch (err) {
      console.error('Upload error:', err)
      setError(getFetchErrorMessage(err))
      setIsProcessing(false)
    }
  }

  const handleCopyTranscription = () => {
    if (result && result.filler_detection && result.filler_detection.transcription) {
      navigator.clipboard.writeText(result.filler_detection.transcription)
      alert('✅ Transcription copiée dans le presse-papier !')
    } else {
      alert('❌ Aucune transcription disponible')
    }
  }

  const handleGenerateTitles = async () => {
    if (!jobId) {
      setError('Aucun job ID disponible')
      return
    }

    if (!result || !result.filler_detection || !result.filler_detection.transcription) {
      setError('Veuillez d\'abord traiter une vidéo avec détection des "euh" activée')
      return
    }

    setIsGeneratingTitles(true)
    setError(null)

    try {
      const response = await fetch(`/api/generate-titles/${jobId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transcription: result.filler_detection.transcription
        })
      })

      if (!response.ok) {
        throw new Error(`Erreur de génération: ${response.statusText}`)
      }

      const data = await response.json()
      setGeneratedTitles(data)
      setIsGeneratingTitles(false)

    } catch (err) {
      console.error('Title generation error:', err)
      setError(getFetchErrorMessage(err))
      setIsGeneratingTitles(false)
    }
  }

  const handleCopyTitle = (index, titleText) => {
    navigator.clipboard.writeText(titleText)
    setCopiedTitleIndex(index)
    setTimeout(() => setCopiedTitleIndex(null), 2000)
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
    <div className="App">
      <header className="App-header">
        <h1>🎬 AutoCut - Édition Vidéo Automatique</h1>
        <p>Supprimez automatiquement les silences et hésitations de vos vidéos</p>
      </header>

      {!file && !result && (
        <div className="upload-section">
          <div
            className={`drop-zone ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="drop-zone-content">
              <div className="upload-icon">📁</div>
              <p className="drop-text">
                Glissez-déposez votre vidéo ici
              </p>
              <p className="drop-subtext">ou cliquez pour parcourir</p>
              <p className="supported-formats">Formats supportés: MP4, MOV</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp4,.mov"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>
        </div>
      )}

      {file && !result && (
        <div className="file-selected">
          <div className="file-info">
            <div className="file-icon">🎥</div>
            <div className="file-details">
              <h3>{file.name}</h3>
              <p>{formatFileSize(file.size)}</p>
            </div>
            <button
              className="remove-btn"
              onClick={handleRemoveFile}
              disabled={isProcessing}
            >
              ✕
            </button>
          </div>

          {/* Preset Selection */}
          <div className="preset-section">
            <h3>⚡ Niveau de Coupe</h3>
            <div className="preset-slider-container">
              <input
                type="range"
                min="1"
                max="5"
                value={presetLevel}
                onChange={(e) => handlePresetChange(parseInt(e.target.value))}
                className="preset-slider"
                disabled={isProcessing}
              />
              <div className="preset-labels">
                {[1, 2, 3, 4, 5].map(level => (
                  <span
                    key={level}
                    className={`preset-label ${presetLevel === level ? 'active' : ''}`}
                  >
                    {presets[level].label}
                  </span>
                ))}
              </div>
            </div>
            <p className="preset-description">
              {presets[presetLevel].description}
            </p>
          </div>

          {/* Advanced Settings */}
          <div className="advanced-section">
            <button
              className="advanced-toggle"
              onClick={() => setAdvancedMode(!advancedMode)}
            >
              {advancedMode ? '▼' : '▶'} Paramètres avancés
            </button>

            {advancedMode && (
              <div className="advanced-settings">
                {/* Filler Words Detection */}
                <div className="setting-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={settings.detectFillerWords}
                      onChange={(e) => setSettings({ ...settings, detectFillerWords: e.target.checked })}
                      disabled={isProcessing}
                    />
                    <span>Détecter les hésitations (euh, hum, etc.)</span>
                  </label>
                </div>

                {settings.detectFillerWords && (
                  <>
                    <div className="setting-group">
                      <label>
                        Sensibilité de détection des "euh": {settings.fillerSensitivity.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0.3"
                        max="1.0"
                        step="0.1"
                        value={settings.fillerSensitivity}
                        onChange={(e) => setSettings({ ...settings, fillerSensitivity: parseFloat(e.target.value) })}
                        disabled={isProcessing}
                      />
                    </div>

                    <div className="setting-group">
                      <label>Modèle Whisper:</label>
                      <select
                        value={settings.whisperModel}
                        onChange={(e) => setSettings({ ...settings, whisperModel: e.target.value })}
                        disabled={isProcessing}
                      >
                        <option value="tiny">Tiny (rapide)</option>
                        <option value="base">Base (recommandé)</option>
                        <option value="small">Small (précis)</option>
                        <option value="medium">Medium (très précis)</option>
                      </select>
                    </div>
                  </>
                )}

                {/* Audio Enhancement */}
                <div className="setting-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={settings.enableAudioEnhancement}
                      onChange={(e) => setSettings({ ...settings, enableAudioEnhancement: e.target.checked })}
                      disabled={isProcessing}
                    />
                    <span>Réduction du bruit audio</span>
                  </label>
                </div>

                {/* Manual Settings */}
                <div className="setting-group">
                  <label>
                    Seuil de silence: {settings.silenceThreshold} dB
                  </label>
                  <input
                    type="range"
                    min="-60"
                    max="-20"
                    value={settings.silenceThreshold}
                    onChange={(e) => setSettings({ ...settings, silenceThreshold: parseInt(e.target.value) })}
                    disabled={isProcessing}
                  />
                </div>

                <div className="setting-group">
                  <label>
                    Durée minimale silence: {settings.minSilenceDuration} ms
                  </label>
                  <input
                    type="range"
                    min="100"
                    max="2000"
                    step="100"
                    value={settings.minSilenceDuration}
                    onChange={(e) => setSettings({ ...settings, minSilenceDuration: parseInt(e.target.value) })}
                    disabled={isProcessing}
                  />
                </div>

                <div className="setting-group">
                  <label>
                    Padding (marge): {settings.padding} ms
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="500"
                    step="25"
                    value={settings.padding}
                    onChange={(e) => setSettings({ ...settings, padding: parseInt(e.target.value) })}
                    disabled={isProcessing}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Process Button */}
          <button
            className="process-btn"
            onClick={handleProcess}
            disabled={isProcessing}
          >
            {isProcessing ? 'Traitement en cours...' : '🚀 Lancer le traitement'}
          </button>

          {/* Progress */}
          {isProcessing && (
            <div className="progress-section">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="progress-text">
                {progressMessage} ({progress}%)
              </p>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="results-section">
          <h2>✅ Traitement terminé !</h2>

          {/* Video Stats */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <div className="stat-label">Durée originale</div>
                <div className="stat-value">{formatTime(result.original_duration)}</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">✂️</div>
              <div className="stat-content">
                <div className="stat-label">Durée finale</div>
                <div className="stat-value">{formatTime(result.final_duration)}</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">💾</div>
              <div className="stat-content">
                <div className="stat-label">Temps économisé</div>
                <div className="stat-value">{formatTime(result.time_saved)}</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">🎯</div>
              <div className="stat-content">
                <div className="stat-label">Segments coupés</div>
                <div className="stat-value">{result.cuts_count}</div>
              </div>
            </div>
          </div>

          {/* Filler Words Detection */}
          {result.filler_detection && (
            <div className="filler-section">
              <h3>🗣️ Détection des hésitations</h3>
              <div className="filler-stats">
                <p><strong>{result.filler_detection.total_fillers}</strong> hésitations détectées et supprimées</p>
              </div>

              {/* Transcription with Copy Button */}
              {result.filler_detection.transcription && (
                <div className="transcription-container">
                  <div className="transcription-header">
                    <h4>📝 Transcription</h4>
                    <button
                      className="copy-btn"
                      onClick={handleCopyTranscription}
                    >
                      📋 Copier le texte
                    </button>
                  </div>
                  <div className="transcription-text">
                    {result.filler_detection.transcription}
                  </div>
                </div>
              )}

              {/* Title Generation Section */}
              <div className="title-generation-section">
                <h4>🎯 Génération de Titres YouTube (A/B Testing)</h4>
                <p className="title-gen-description">
                  Générez 3 titres optimisés pour maximiser le taux de clic sur YouTube
                </p>

                <button
                  className="generate-titles-btn"
                  onClick={handleGenerateTitles}
                  disabled={isGeneratingTitles}
                >
                  {isGeneratingTitles ? '⏳ Génération en cours...' : '✨ Générer 3 Titres Optimisés'}
                </button>

                {generatedTitles && generatedTitles.titles && (
                  <div className="generated-titles">
                    <div className="titles-header">
                      <strong>🎬 Titres générés</strong>
                      <span className="ai-badge">
                        {generatedTitles.source === 'local_ai' ? '🤖 IA Locale' : '📝 Automatique'}
                      </span>
                    </div>

                    {generatedTitles.titles.map((title, index) => (
                      <div key={index} className="title-card">
                        <div className="title-header">
                          <span className="title-type">{title.type}</span>
                          <span className="title-length">{title.length} caractères</span>
                        </div>
                        <div className="title-text">{title.text}</div>
                        <button
                          className={`copy-title-btn ${copiedTitleIndex === index ? 'copied' : ''}`}
                          onClick={() => handleCopyTitle(index, title.text)}
                        >
                          {copiedTitleIndex === index ? '✅ Copié !' : '📋 Copier'}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Download Section */}
          <div className="download-section">
            <h3>📥 Télécharger les résultats</h3>
            <div className="download-buttons">
              <a
                href={`/api/download/${jobId}`}
                download
                className="download-btn primary"
              >
                🎥 Télécharger la vidéo
              </a>
              <a
                href={`/api/export/${jobId}/premiere`}
                download
                className="download-btn"
              >
                📋 Export Premiere Pro (XML)
              </a>
              <a
                href={`/api/export/${jobId}/finalcut`}
                download
                className="download-btn"
              >
                📋 Export Final Cut Pro (XML)
              </a>
            </div>
          </div>

          <button
            className="process-btn"
            onClick={handleRemoveFile}
            style={{ marginTop: '30px' }}
          >
            Traiter une autre vidéo
          </button>
        </div>
      )}

      {error && (
        <div className="error">
          <strong>❌ Erreur:</strong> {error}
        </div>
      )}

      <style jsx>{`
        .App {
          min-height: 100vh;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          color: #fff;
          padding: 20px;
        }

        .App-header {
          text-align: center;
          margin-bottom: 40px;
        }

        .App-header h1 {
          font-size: 2.5rem;
          margin-bottom: 10px;
        }

        .App-header p {
          font-size: 1.1rem;
          color: #aaa;
        }

        .upload-section {
          max-width: 600px;
          margin: 0 auto;
        }

        .drop-zone {
          border: 3px dashed #4a5568;
          border-radius: 12px;
          padding: 60px 20px;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s ease;
          background: rgba(255, 255, 255, 0.05);
        }

        .drop-zone:hover {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.1);
        }

        .drop-zone.dragging {
          border-color: #10b981;
          background: rgba(16, 185, 129, 0.1);
        }

        .upload-icon {
          font-size: 4rem;
          margin-bottom: 20px;
        }

        .drop-text {
          font-size: 1.3rem;
          margin-bottom: 8px;
        }

        .drop-subtext {
          color: #888;
          margin-bottom: 20px;
        }

        .supported-formats {
          font-size: 0.9rem;
          color: #666;
        }

        .file-selected {
          max-width: 800px;
          margin: 0 auto;
        }

        .file-info {
          display: flex;
          align-items: center;
          background: rgba(255, 255, 255, 0.05);
          padding: 20px;
          border-radius: 12px;
          margin-bottom: 30px;
        }

        .file-icon {
          font-size: 3rem;
          margin-right: 20px;
        }

        .file-details {
          flex: 1;
        }

        .file-details h3 {
          margin: 0 0 5px 0;
          font-size: 1.2rem;
        }

        .file-details p {
          margin: 0;
          color: #888;
        }

        .remove-btn {
          background: #ef4444;
          color: #fff;
          border: none;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 1.2rem;
          transition: all 0.2s;
        }

        .remove-btn:hover:not(:disabled) {
          background: #dc2626;
        }

        .remove-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .preset-section {
          background: rgba(255, 255, 255, 0.05);
          padding: 25px;
          border-radius: 12px;
          margin-bottom: 20px;
        }

        .preset-section h3 {
          margin-top: 0;
          margin-bottom: 20px;
        }

        .preset-slider-container {
          margin-bottom: 15px;
        }

        .preset-slider {
          width: 100%;
          height: 8px;
          border-radius: 4px;
          background: #334155;
          outline: none;
          -webkit-appearance: none;
        }

        .preset-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }

        .preset-slider::-moz-range-thumb {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }

        .preset-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 10px;
        }

        .preset-label {
          font-size: 0.85rem;
          color: #888;
          transition: all 0.2s;
        }

        .preset-label.active {
          color: #3b82f6;
          font-weight: bold;
        }

        .preset-description {
          text-align: center;
          color: #aaa;
          margin-top: 10px;
          font-size: 0.95rem;
        }

        .advanced-section {
          background: rgba(255, 255, 255, 0.05);
          padding: 20px;
          border-radius: 12px;
          margin-bottom: 20px;
        }

        .advanced-toggle {
          background: none;
          border: none;
          color: #3b82f6;
          font-size: 1rem;
          cursor: pointer;
          padding: 0;
        }

        .advanced-settings {
          margin-top: 20px;
        }

        .setting-group {
          margin-bottom: 20px;
        }

        .setting-group label {
          display: block;
          margin-bottom: 8px;
          color: #ddd;
        }

        .setting-group input[type="range"] {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: #334155;
          outline: none;
          -webkit-appearance: none;
        }

        .setting-group input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }

        .setting-group input[type="range"]::-moz-range-thumb {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }

        .setting-group input[type="checkbox"] {
          margin-right: 10px;
        }

        .setting-group select {
          width: 100%;
          padding: 10px;
          background: #1e293b;
          color: #fff;
          border: 1px solid #334155;
          border-radius: 6px;
          font-size: 1rem;
        }

        .process-btn {
          width: 100%;
          padding: 18px;
          background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
          color: #fff;
          border: none;
          border-radius: 12px;
          font-size: 1.2rem;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s;
        }

        .process-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
        }

        .process-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .progress-section {
          margin-top: 20px;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: #334155;
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
          transition: width 0.3s ease;
        }

        .progress-text {
          text-align: center;
          margin-top: 10px;
          color: #aaa;
        }

        .results-section {
          max-width: 900px;
          margin: 0 auto;
        }

        .results-section h2 {
          text-align: center;
          font-size: 2rem;
          margin-bottom: 30px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .stat-card {
          background: rgba(255, 255, 255, 0.05);
          padding: 20px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .stat-icon {
          font-size: 2.5rem;
        }

        .stat-content {
          flex: 1;
        }

        .stat-label {
          font-size: 0.9rem;
          color: #888;
          margin-bottom: 5px;
        }

        .stat-value {
          font-size: 1.5rem;
          font-weight: bold;
          color: #3b82f6;
        }

        .filler-section {
          background: rgba(255, 255, 255, 0.05);
          padding: 25px;
          border-radius: 12px;
          margin-bottom: 30px;
        }

        .filler-section h3 {
          margin-top: 0;
          margin-bottom: 15px;
        }

        .filler-stats {
          margin-bottom: 20px;
        }

        .transcription-container {
          background: rgba(0, 0, 0, 0.3);
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 25px;
        }

        .transcription-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }

        .transcription-header h4 {
          margin: 0;
        }

        .copy-btn {
          background: #10b981;
          color: #fff;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          cursor: pointer;
          font-weight: bold;
          transition: all 0.2s;
        }

        .copy-btn:hover {
          background: #059669;
        }

        .transcription-text {
          background: rgba(0, 0, 0, 0.4);
          padding: 15px;
          border-radius: 6px;
          line-height: 1.6;
          max-height: 200px;
          overflow-y: auto;
          color: #ddd;
        }

        .title-generation-section {
          background: rgba(59, 130, 246, 0.1);
          border: 2px solid rgba(59, 130, 246, 0.3);
          padding: 20px;
          border-radius: 12px;
          margin-top: 25px;
        }

        .title-generation-section h4 {
          margin-top: 0;
          margin-bottom: 10px;
        }

        .title-gen-description {
          color: #aaa;
          margin-bottom: 20px;
        }

        .generate-titles-btn {
          width: 100%;
          padding: 15px;
          background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
          color: #fff;
          border: none;
          border-radius: 8px;
          font-size: 1.1rem;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s;
        }

        .generate-titles-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 16px rgba(139, 92, 246, 0.3);
        }

        .generate-titles-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .generated-titles {
          margin-top: 20px;
        }

        .titles-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }

        .ai-badge {
          background: rgba(139, 92, 246, 0.2);
          color: #a78bfa;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 0.85rem;
        }

        .title-card {
          background: rgba(0, 0, 0, 0.3);
          padding: 15px;
          border-radius: 8px;
          margin-bottom: 15px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .title-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .title-type {
          background: rgba(59, 130, 246, 0.2);
          color: #60a5fa;
          padding: 4px 10px;
          border-radius: 8px;
          font-size: 0.85rem;
          font-weight: bold;
        }

        .title-length {
          color: #888;
          font-size: 0.85rem;
        }

        .title-text {
          font-size: 1.1rem;
          margin-bottom: 12px;
          line-height: 1.4;
        }

        .copy-title-btn {
          background: #10b981;
          color: #fff;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          cursor: pointer;
          font-weight: bold;
          font-size: 0.9rem;
          transition: all 0.2s;
        }

        .copy-title-btn:hover {
          background: #059669;
        }

        .copy-title-btn.copied {
          background: #6366f1;
        }

        .download-section {
          background: rgba(255, 255, 255, 0.05);
          padding: 25px;
          border-radius: 12px;
          margin-bottom: 30px;
        }

        .download-section h3 {
          margin-top: 0;
          margin-bottom: 20px;
        }

        .download-buttons {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .download-btn {
          padding: 15px 30px;
          background: #334155;
          color: #fff;
          text-decoration: none;
          border-radius: 8px;
          text-align: center;
          font-weight: bold;
          transition: all 0.2s;
        }

        .download-btn:hover {
          background: #475569;
          transform: translateY(-2px);
        }

        .download-btn.primary {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }

        .download-btn.primary:hover {
          background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }

        .error {
          max-width: 600px;
          margin: 30px auto;
          padding: 20px;
          background: rgba(239, 68, 68, 0.1);
          border: 2px solid #ef4444;
          border-radius: 12px;
          color: #fca5a5;
        }
      `}</style>
    </div>
  )
}

export default App

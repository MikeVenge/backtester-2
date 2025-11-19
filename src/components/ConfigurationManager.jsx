import React, { useState, useEffect } from 'react'
import './ConfigurationManager.css'

function ConfigurationManager({ formData, currentConfigName, onLoadConfiguration, onSaveConfiguration, onConfigNameChange }) {
  const [savedConfigs, setSavedConfigs] = useState([])
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [configName, setConfigName] = useState('')
  const [showLoadModal, setShowLoadModal] = useState(false)

  useEffect(() => {
    loadSavedConfigurations()
  }, [])

  const loadSavedConfigurations = () => {
    try {
      const saved = localStorage.getItem('backtester-configurations')
      if (saved) {
        const configs = JSON.parse(saved)
        setSavedConfigs(configs)
      }
    } catch (error) {
      console.error('Error loading configurations:', error)
    }
  }

  const handleSave = () => {
    if (!configName.trim()) {
      alert('Please enter a configuration name')
      return
    }

    const isUpdate = savedConfigs.some(c => c.name === configName.trim())
    const configs = savedConfigs.filter(c => c.name !== configName.trim())
    
    const newConfig = {
      name: configName.trim(),
      data: formData,
      createdAt: isUpdate 
        ? savedConfigs.find(c => c.name === configName.trim())?.createdAt || new Date().toISOString()
        : new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }

    const updatedConfigs = [...configs, newConfig]
    localStorage.setItem('backtester-configurations', JSON.stringify(updatedConfigs))
    setSavedConfigs(updatedConfigs)
    setConfigName('')
    setShowSaveModal(false)
    if (onConfigNameChange) {
      onConfigNameChange(configName.trim())
    }
    alert(`Configuration "${configName}" ${isUpdate ? 'updated' : 'saved'} successfully!`)
  }

  const handleOpenSaveModal = () => {
    // Pre-fill with current config name if one is loaded
    if (currentConfigName) {
      setConfigName(currentConfigName)
    }
    setShowSaveModal(true)
  }

  const handleLoad = (config) => {
    if (window.confirm(`Load configuration "${config.name}"? This will replace your current settings.`)) {
      onLoadConfiguration(config.data, config.name)
      setShowLoadModal(false)
    }
  }

  const handleDelete = (configName, e) => {
    e.stopPropagation()
    if (window.confirm(`Delete configuration "${configName}"?`)) {
      const updatedConfigs = savedConfigs.filter(c => c.name !== configName)
      localStorage.setItem('backtester-configurations', JSON.stringify(updatedConfigs))
      setSavedConfigs(updatedConfigs)
    }
  }

  const handleUpdate = (config) => {
    if (window.confirm(`Update configuration "${config.name}" with current settings?`)) {
      const updatedConfigs = savedConfigs.map(c => 
        c.name === config.name 
          ? { ...c, data: formData, updatedAt: new Date().toISOString() }
          : c
      )
      localStorage.setItem('backtester-configurations', JSON.stringify(updatedConfigs))
      setSavedConfigs(updatedConfigs)
      if (onConfigNameChange && currentConfigName === config.name) {
        // Keep the same config name if we're updating the current one
        onConfigNameChange(config.name)
      }
      alert(`Configuration "${config.name}" updated successfully!`)
    }
  }

  const handleRun = () => {
    // Check if there's any configuration data
    const hasData = Object.keys(formData).length > 0 && 
                    Object.values(formData).some(section => 
                      section && Object.keys(section).length > 0
                    )
    
    if (!hasData) {
      alert('Please configure at least one section before running the backtest.')
      return
    }

    // Export configuration for running
    const configToRun = {
      name: 'Current Configuration',
      data: formData,
      timestamp: new Date().toISOString()
    }
    
    // For now, we'll show an alert. In the future, this can trigger actual backtest execution
    console.log('Running backtest with configuration:', configToRun)
    alert(`Backtest configuration is ready to run!\n\nConfiguration data has been logged to console.\n\nIn the future, this will trigger the actual backtest execution.`)
  }

  return (
    <div className="config-manager">
      {currentConfigName && (
        <div className="current-config-indicator">
          <span className="config-label">Current Configuration:</span>
          <span className="config-name-display">{currentConfigName}</span>
          <button 
            className="btn-clear-config"
            onClick={() => {
              if (window.confirm('Clear current configuration? This will reset all form data.')) {
                onLoadConfiguration({}, null)
              }
            }}
            title="Clear current configuration"
          >
            ✕ Clear
          </button>
        </div>
      )}
      <div className="config-buttons">
        <button 
          className="btn btn-run"
          onClick={handleRun}
        >
          ▶️ Run Backtest
        </button>
        <button 
          className="btn btn-primary"
          onClick={handleOpenSaveModal}
        >
          💾 {currentConfigName ? 'Update Configuration' : 'Save Configuration'}
        </button>
        <button 
          className="btn btn-secondary"
          onClick={() => setShowLoadModal(true)}
        >
          📂 Load Configuration
        </button>
      </div>

      {showSaveModal && (
        <div className="modal-overlay" onClick={() => setShowSaveModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Save Configuration</h3>
            <div className="form-group">
              <label>Configuration Name</label>
              <input
                type="text"
                placeholder="e.g., Momentum Strategy v1"
                value={configName}
                onChange={(e) => setConfigName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSave()}
                autoFocus
              />
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={handleSave}>
                Save
              </button>
              <button className="btn btn-secondary" onClick={() => setShowSaveModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showLoadModal && (
        <div className="modal-overlay" onClick={() => setShowLoadModal(false)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h3>Load Configuration</h3>
            {savedConfigs.length === 0 ? (
              <p className="no-configs">No saved configurations found.</p>
            ) : (
              <div className="config-list">
                {savedConfigs.map((config, index) => (
                  <div key={index} className="config-item">
                    <div className="config-info" onClick={() => handleLoad(config)}>
                      <div className="config-name">{config.name}</div>
                      <div className="config-meta">
                        Created: {new Date(config.createdAt).toLocaleString()}
                        {config.updatedAt !== config.createdAt && (
                          <span> • Updated: {new Date(config.updatedAt).toLocaleString()}</span>
                        )}
                      </div>
                    </div>
                    <div className="config-actions">
                      <button 
                        className="btn btn-small btn-load"
                        onClick={() => handleLoad(config)}
                        title="Load and edit this configuration"
                      >
                        📂 Load
                      </button>
                      <button 
                        className="btn btn-small btn-update"
                        onClick={() => handleUpdate(config)}
                        title="Update with current settings"
                      >
                        ↻ Update
                      </button>
                      <button 
                        className="btn btn-small btn-delete"
                        onClick={(e) => handleDelete(config.name, e)}
                        title="Delete configuration"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowLoadModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ConfigurationManager


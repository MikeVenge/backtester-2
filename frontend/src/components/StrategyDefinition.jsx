import React from 'react'
import './FormSection.css'

function StrategyDefinition({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    const updatedData = {
      ...data,
      [field]: value
    }
    
    // Sync Entry Logic with FinChat Entry Prompt when in prompt string mode
    if (field === 'entryLogic' && data.entryPromptType === 'string') {
      updatedData.entryFinChatPrompt = value
    }
    if (field === 'entryFinChatPrompt' && data.entryPromptType === 'string') {
      updatedData.entryLogic = value
    }
    
    // Sync Exit Logic with FinChat Exit Prompt when in prompt string mode
    if (field === 'exitLogic' && data.exitPromptType === 'string') {
      updatedData.exitFinChatPrompt = value
    }
    if (field === 'exitFinChatPrompt' && data.exitPromptType === 'string') {
      updatedData.exitLogic = value
    }
    
    onChange(updatedData)
  }

  return (
    <div className="form-section">
      <h2>Strategy Definition</h2>
      
      <div className="form-section-divider">
        <h3>Entry Rules</h3>
      </div>

      <div className="form-group">
        <label>FinChat Entry Prompt</label>
        <div className="prompt-type-selector">
          <label className="radio-label">
            <input
              type="radio"
              name="entryPromptType"
              value="url"
              checked={(data.entryPromptType || 'url') === 'url'}
              onChange={(e) => handleChange('entryPromptType', e.target.value)}
            />
            URL
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="entryPromptType"
              value="string"
              checked={data.entryPromptType === 'string'}
              onChange={(e) => handleChange('entryPromptType', e.target.value)}
            />
            Prompt String
          </label>
        </div>
        {(!data.entryPromptType || data.entryPromptType === 'url') ? (
          <input
            type="url"
            placeholder="e.g., https://finchat.io/prompt/abc123"
            value={data.entryFinChatUrl || ''}
            onChange={(e) => handleChange('entryFinChatUrl', e.target.value)}
          />
        ) : (
          <textarea
            rows="6"
            placeholder="Paste your FinChat prompt string here..."
            value={data.entryFinChatPrompt || data.entryLogic || ''}
            onChange={(e) => {
              const value = e.target.value
              // In prompt string mode, update both fields
              onChange({
                ...data,
                entryLogic: value,
                entryFinChatPrompt: value
              })
            }}
          />
        )}
        <small>
          {data.entryPromptType === 'string' 
            ? 'FinChat prompt string for entry conditions'
            : 'FinChat prompt URL for entry conditions'}
        </small>
      </div>

      <div className="form-section-divider">
        <h3>Exit Rules</h3>
      </div>

      <div className="form-group">
        <label>FinChat Exit Prompt</label>
        <div className="prompt-type-selector">
          <label className="radio-label">
            <input
              type="radio"
              name="exitPromptType"
              value="url"
              checked={(data.exitPromptType || 'url') === 'url'}
              onChange={(e) => handleChange('exitPromptType', e.target.value)}
            />
            URL
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="exitPromptType"
              value="string"
              checked={data.exitPromptType === 'string'}
              onChange={(e) => {
                handleChange('exitPromptType', e.target.value)
                // When switching to prompt string mode, sync with Exit Logic if it exists
                if (e.target.value === 'string' && data.exitLogic && !data.exitFinChatPrompt) {
                  handleChange('exitFinChatPrompt', data.exitLogic)
                }
              }}
            />
            Prompt String
          </label>
        </div>
        {(!data.exitPromptType || data.exitPromptType === 'url') ? (
          <input
            type="url"
            placeholder="e.g., https://finchat.io/prompt/xyz789"
            value={data.exitFinChatUrl || ''}
            onChange={(e) => handleChange('exitFinChatUrl', e.target.value)}
          />
        ) : (
          <textarea
            rows="6"
            placeholder="Paste your FinChat prompt string here..."
            value={data.exitFinChatPrompt || data.exitLogic || ''}
            onChange={(e) => {
              const value = e.target.value
              // In prompt string mode, update both fields
              onChange({
                ...data,
                exitLogic: value,
                exitFinChatPrompt: value
              })
            }}
          />
        )}
        <small>
          {data.exitPromptType === 'string'
            ? 'FinChat prompt string for exit conditions'
            : 'FinChat prompt URL for exit conditions'}
        </small>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Take-Profit (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 10"
            value={data.takeProfit || ''}
            onChange={(e) => handleChange('takeProfit', e.target.value)}
          />
        </div>
        <div className="form-group">
          <label>Stop-Loss (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 5"
            value={data.stopLoss || ''}
            onChange={(e) => handleChange('stopLoss', e.target.value)}
          />
        </div>
      </div>

      <div className="form-group">
        <label>Time-Based Exit (days)</label>
        <input
          type="number"
          placeholder="e.g., 5"
          value={data.timeBasedExit || ''}
          onChange={(e) => handleChange('timeBasedExit', e.target.value)}
        />
        <small>Hold for X days before exit (optional)</small>
      </div>

      <div className="form-section-divider">
        <h3>Position Sizing Rules</h3>
      </div>

      <div className="form-group">
        <label>Position Sizing Method</label>
        <select
          value={data.positionSizingMethod || ''}
          onChange={(e) => handleChange('positionSizingMethod', e.target.value)}
        >
          <option value="">Select method</option>
          <option value="fixed-dollar">Fixed Dollar Amount</option>
          <option value="portfolio-percent">Percentage of Portfolio</option>
          <option value="risk-based">Risk-Based (e.g., 1% of equity per trade)</option>
        </select>
      </div>

      {data.positionSizingMethod === 'fixed-dollar' && (
        <div className="form-group">
          <label>Fixed Dollar Amount ($)</label>
          <input
            type="number"
            placeholder="e.g., 1000"
            value={data.fixedDollarAmount || ''}
            onChange={(e) => handleChange('fixedDollarAmount', e.target.value)}
          />
        </div>
      )}

      {data.positionSizingMethod === 'portfolio-percent' && (
        <div className="form-group">
          <label>Portfolio Percentage (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 10"
            value={data.portfolioPercent || ''}
            onChange={(e) => handleChange('portfolioPercent', e.target.value)}
          />
        </div>
      )}

      {data.positionSizingMethod === 'risk-based' && (
        <div className="form-group">
          <label>Risk Percentage (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 1"
            value={data.riskPercent || ''}
            onChange={(e) => handleChange('riskPercent', e.target.value)}
          />
          <small>Percentage of equity to risk per trade</small>
        </div>
      )}

      <div className="form-group">
        <label>Max Concurrent Positions</label>
        <input
          type="number"
          placeholder="e.g., 10"
          value={data.maxPositions || ''}
          onChange={(e) => handleChange('maxPositions', e.target.value)}
        />
      </div>

      <div className="form-section-divider">
        <h3>Universe / Selection Rules (for multi-asset strategies)</h3>
      </div>

      <div className="form-group">
        <label>Eligible Symbols</label>
        <textarea
          rows="3"
          placeholder="e.g., All S&P 500 stocks, or list specific symbols"
          value={data.eligibleSymbols || ''}
          onChange={(e) => handleChange('eligibleSymbols', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Ranking / Filtering Logic</label>
        <textarea
          rows="3"
          placeholder="e.g., Top 10 by momentum, filter by market cap > $1B"
          value={data.rankingLogic || ''}
          onChange={(e) => handleChange('rankingLogic', e.target.value)}
        />
      </div>
    </div>
  )
}

export default StrategyDefinition


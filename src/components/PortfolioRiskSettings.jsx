import React from 'react'
import './FormSection.css'

function PortfolioRiskSettings({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    onChange({
      ...data,
      [field]: value
    })
  }

  return (
    <div className="form-section">
      <h2>Portfolio & Risk Settings</h2>
      
      <div className="form-group">
        <label>Initial Capital</label>
        <input
          type="number"
          placeholder="e.g., 10000"
          value={data.initialCapital || ''}
          onChange={(e) => handleChange('initialCapital', e.target.value)}
        />
        <small>Starting cash (e.g., $10,000 or 1 BTC)</small>
      </div>

      <div className="form-section-divider">
        <h3>Leverage</h3>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.leverageAllowed || false}
            onChange={(e) => handleChange('leverageAllowed', e.target.checked)}
          />
          Allow Leverage
        </label>
      </div>

      {data.leverageAllowed && (
        <div className="form-group">
          <label>Max Leverage (x)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 2"
            value={data.maxLeverage || ''}
            onChange={(e) => handleChange('maxLeverage', e.target.value)}
          />
        </div>
      )}

      <div className="form-section-divider">
        <h3>Position & Exposure Limits</h3>
      </div>

      <div className="form-group">
        <label>Max % in Single Asset</label>
        <input
          type="number"
          step="0.1"
          placeholder="e.g., 20"
          value={data.maxSingleAssetPercent || ''}
          onChange={(e) => handleChange('maxSingleAssetPercent', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Max % in Sector</label>
        <input
          type="number"
          step="0.1"
          placeholder="e.g., 30"
          value={data.maxSectorPercent || ''}
          onChange={(e) => handleChange('maxSectorPercent', e.target.value)}
        />
        <small>If relevant for your strategy</small>
      </div>

      <div className="form-group">
        <label>Max Net Long/Short Exposure (%)</label>
        <input
          type="number"
          step="0.1"
          placeholder="e.g., 100"
          value={data.maxNetExposure || ''}
          onChange={(e) => handleChange('maxNetExposure', e.target.value)}
        />
      </div>

      <div className="form-section-divider">
        <h3>Risk Management Rules</h3>
      </div>

      <div className="form-group">
        <label>Stop-Loss Type</label>
        <select
          value={data.stopLossType || ''}
          onChange={(e) => handleChange('stopLossType', e.target.value)}
        >
          <option value="">Select type</option>
          <option value="fixed-percent">Fixed Percentage</option>
          <option value="volatility-based">Volatility-Based</option>
          <option value="dollar-based">Dollar-Based</option>
        </select>
      </div>

      <div className="form-group">
        <label>Take-Profit Rules</label>
        <textarea
          rows="3"
          placeholder="Describe take-profit logic"
          value={data.takeProfitRules || ''}
          onChange={(e) => handleChange('takeProfitRules', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.useTrailingStops || false}
            onChange={(e) => handleChange('useTrailingStops', e.target.checked)}
          />
          Use Trailing Stops
        </label>
      </div>

      {data.useTrailingStops && (
        <div className="form-group">
          <label>Trailing Stop Distance (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 2"
            value={data.trailingStopDistance || ''}
            onChange={(e) => handleChange('trailingStopDistance', e.target.value)}
          />
        </div>
      )}

      <div className="form-row">
        <div className="form-group">
          <label>Max Daily Drawdown (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 5"
            value={data.maxDailyDrawdown || ''}
            onChange={(e) => handleChange('maxDailyDrawdown', e.target.value)}
          />
        </div>
        <div className="form-group">
          <label>Max Weekly Drawdown (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 10"
            value={data.maxWeeklyDrawdown || ''}
            onChange={(e) => handleChange('maxWeeklyDrawdown', e.target.value)}
          />
        </div>
      </div>
    </div>
  )
}

export default PortfolioRiskSettings


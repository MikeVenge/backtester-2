import React from 'react'
import './FormSection.css'

function MTMSettings({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    onChange({
      ...data,
      [field]: value
    })
  }

  return (
    <div className="form-section">
      <h2>Mark-to-Market (MTM) Settings</h2>
      
      <div className="form-section-divider">
        <h3>MTM Frequency</h3>
      </div>

      <div className="form-group">
        <label>MTM Frequency</label>
        <select
          value={data.mtmFrequency || ''}
          onChange={(e) => handleChange('mtmFrequency', e.target.value)}
        >
          <option value="">Select frequency</option>
          <option value="every-bar">Every Bar (most common)</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
        <small>Recompute portfolio value at this frequency</small>
      </div>

      <div className="form-section-divider">
        <h3>Price Used for MTM</h3>
      </div>

      <div className="form-group">
        <label>MTM Price</label>
        <select
          value={data.mtmPrice || ''}
          onChange={(e) => handleChange('mtmPrice', e.target.value)}
        >
          <option value="">Select price</option>
          <option value="close">Close Price (typical for EOD data)</option>
          <option value="vwap">VWAP</option>
          <option value="mid">Mid Price</option>
          <option value="last">Last Price</option>
          <option value="custom">Custom Rule</option>
        </select>
      </div>

      {data.mtmPrice === 'custom' && (
        <div className="form-group">
          <label>Custom MTM Rule</label>
          <textarea
            rows="3"
            placeholder="e.g., mark long at bid, short at ask"
            value={data.customMTMRule || ''}
            onChange={(e) => handleChange('customMTMRule', e.target.value)}
          />
        </div>
      )}

      <div className="form-section-divider">
        <h3>FX / Multi-Currency MTM (if relevant)</h3>
      </div>

      <div className="form-group">
        <label>Base Currency</label>
        <input
          type="text"
          placeholder="e.g., USD"
          value={data.baseCurrency || ''}
          onChange={(e) => handleChange('baseCurrency', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>FX Rates Source & Frequency</label>
        <select
          value={data.fxFrequency || ''}
          onChange={(e) => handleChange('fxFrequency', e.target.value)}
        >
          <option value="">Select frequency</option>
          <option value="daily">Daily</option>
          <option value="intraday">Intraday</option>
        </select>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.mtmFXSeparately || false}
            onChange={(e) => handleChange('mtmFXSeparately', e.target.checked)}
          />
          MTM FX Exposures Separately
        </label>
      </div>

      <div className="form-section-divider">
        <h3>Corporate Action Handling</h3>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.adjustForSplitsDividends || false}
            onChange={(e) => handleChange('adjustForSplitsDividends', e.target.checked)}
          />
          Adjust Historical Prices for Splits / Dividends
        </label>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.bookDividendCashflows || false}
            onChange={(e) => handleChange('bookDividendCashflows', e.target.checked)}
          />
          Explicitly Book Dividend Cashflows on Ex-Date/Pay-Date
        </label>
      </div>
    </div>
  )
}

export default MTMSettings


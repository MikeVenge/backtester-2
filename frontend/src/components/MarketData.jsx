import React from 'react'
import './FormSection.css'

function MarketData({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    onChange({
      ...data,
      [field]: value
    })
  }

  return (
    <div className="form-section">
      <h2>Market Data</h2>
      
      <div className="form-group">
        <label>Ticker(s) / Symbol(s)</label>
        <input
          type="text"
          placeholder="e.g., AAPL, MSFT, GOOGL"
          value={data.tickers || ''}
          onChange={(e) => handleChange('tickers', e.target.value)}
        />
        <small>Comma-separated list of stock symbols</small>
      </div>

      <div className="form-group">
        <label>Data Fields</label>
        <div className="checkbox-group">
          {['Open', 'High', 'Low', 'Close', 'Volume'].map(field => (
            <label key={field} className="checkbox-label">
              <input
                type="checkbox"
                checked={data.fields?.includes(field) || false}
                onChange={(e) => {
                  const fields = data.fields || []
                  if (e.target.checked) {
                    handleChange('fields', [...fields, field])
                  } else {
                    handleChange('fields', fields.filter(f => f !== field))
                  }
                }}
              />
              {field}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Data Frequency</label>
        <select
          value={data.frequency || ''}
          onChange={(e) => handleChange('frequency', e.target.value)}
        >
          <option value="">Select frequency</option>
          <option value="tick">Tick</option>
          <option value="1min">1-minute</option>
          <option value="5min">5-minute</option>
          <option value="hourly">Hourly</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Start Date</label>
          <input
            type="date"
            value={data.startDate || ''}
            onChange={(e) => handleChange('startDate', e.target.value)}
          />
        </div>
        <div className="form-group">
          <label>End Date</label>
          <input
            type="date"
            value={data.endDate || ''}
            onChange={(e) => handleChange('endDate', e.target.value)}
          />
        </div>
      </div>

      <div className="form-section-divider">
        <h3>Corporate Actions (Optional)</h3>
      </div>

      <div className="checkbox-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.includeDividends || false}
            onChange={(e) => handleChange('includeDividends', e.target.checked)}
          />
          Include Dividends
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.includeSplits || false}
            onChange={(e) => handleChange('includeSplits', e.target.checked)}
          />
          Include Splits
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.includeDelistings || false}
            onChange={(e) => handleChange('includeDelistings', e.target.checked)}
          />
          Include Delistings / Mergers
        </label>
      </div>

      <div className="form-section-divider">
        <h3>Benchmark Data (Optional)</h3>
      </div>

      <div className="form-group">
        <label>Benchmark Symbol</label>
        <input
          type="text"
          placeholder="e.g., SPY, BTC"
          value={data.benchmark || ''}
          onChange={(e) => handleChange('benchmark', e.target.value)}
        />
        <small>Index or asset to compare against</small>
      </div>
    </div>
  )
}

export default MarketData


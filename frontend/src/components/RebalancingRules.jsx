import React from 'react'
import './FormSection.css'

function RebalancingRules({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    onChange({
      ...data,
      [field]: value
    })
  }

  return (
    <div className="form-section">
      <h2>Rebalancing Rules</h2>
      
      <div className="form-section-divider">
        <h3>Rebalancing Frequency / Trigger</h3>
      </div>

      <div className="form-group">
        <label>Rebalancing Type</label>
        <select
          value={data.rebalancingType || ''}
          onChange={(e) => handleChange('rebalancingType', e.target.value)}
        >
          <option value="">Select type</option>
          <option value="calendar-based">Calendar-Based</option>
          <option value="threshold-based">Threshold-Based</option>
          <option value="signal-based">Signal-Based</option>
          <option value="hybrid">Hybrid</option>
        </select>
      </div>

      {data.rebalancingType === 'calendar-based' && (
        <>
          <div className="form-group">
            <label>Calendar Frequency</label>
            <select
              value={data.calendarFrequency || ''}
              onChange={(e) => handleChange('calendarFrequency', e.target.value)}
            >
              <option value="">Select frequency</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
            </select>
          </div>
          <div className="form-group">
            <label>Specific Day/Date</label>
            <input
              type="text"
              placeholder="e.g., First trading day of month"
              value={data.specificDay || ''}
              onChange={(e) => handleChange('specificDay', e.target.value)}
            />
          </div>
        </>
      )}

      {data.rebalancingType === 'threshold-based' && (
        <div className="form-group">
          <label>Weight Drift Threshold (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 5"
            value={data.driftThreshold || ''}
            onChange={(e) => handleChange('driftThreshold', e.target.value)}
          />
          <small>Only rebalance if positions deviate > X% from target weights</small>
        </div>
      )}

      {data.rebalancingType === 'signal-based' && (
        <div className="form-group">
          <label>Signal Description</label>
          <textarea
            rows="3"
            placeholder="e.g., Rebalance when ranking changes or entry/exit conditions triggered"
            value={data.signalDescription || ''}
            onChange={(e) => handleChange('signalDescription', e.target.value)}
          />
        </div>
      )}

      {data.rebalancingType === 'hybrid' && (
        <>
          <div className="form-group">
            <label>Check Frequency</label>
            <select
              value={data.hybridCheckFrequency || ''}
              onChange={(e) => handleChange('hybridCheckFrequency', e.target.value)}
            >
              <option value="">Select frequency</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          <div className="form-group">
            <label>Drift Threshold (%)</label>
            <input
              type="number"
              step="0.1"
              placeholder="e.g., 3"
              value={data.hybridDriftThreshold || ''}
              onChange={(e) => handleChange('hybridDriftThreshold', e.target.value)}
            />
          </div>
        </>
      )}

      <div className="form-section-divider">
        <h3>Universe Updates (Adding/Deleting Assets)</h3>
      </div>

      <div className="form-group">
        <label>Rules for Adding New Names</label>
        <textarea
          rows="3"
          placeholder="e.g., Include stocks that meet liquidity and market-cap filters at each monthly rebalance"
          value={data.addRules || ''}
          onChange={(e) => handleChange('addRules', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Rules for Removing Names</label>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={data.dropDelisted || false}
              onChange={(e) => handleChange('dropDelisted', e.target.checked)}
            />
            Drop Delisted / Suspended Assets
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={data.dropBelowThresholds || false}
              onChange={(e) => handleChange('dropBelowThresholds', e.target.checked)}
            />
            Drop Names Below Liquidity/Price Thresholds
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={data.exitIneligible || false}
              onChange={(e) => handleChange('exitIneligible', e.target.checked)}
            />
            Exit Positions in Names That Leave Eligible Universe
          </label>
        </div>
      </div>

      <div className="form-section-divider">
        <h3>Rebalancing Method</h3>
      </div>

      <div className="form-group">
        <label>Rebalancing Method</label>
        <select
          value={data.rebalancingMethod || ''}
          onChange={(e) => handleChange('rebalancingMethod', e.target.value)}
        >
          <option value="">Select method</option>
          <option value="full">Full Rebalance to Target Weights</option>
          <option value="partial">Partial Rebalance / Top-Up</option>
          <option value="buy-only">Buy-Only (DCA-style)</option>
          <option value="turnover-limited">Turnover-Limited</option>
        </select>
      </div>

      {data.rebalancingMethod === 'turnover-limited' && (
        <div className="form-group">
          <label>Max Turnover per Rebalance (%)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g., 20"
            value={data.maxTurnover || ''}
            onChange={(e) => handleChange('maxTurnover', e.target.value)}
          />
        </div>
      )}

      <div className="form-section-divider">
        <h3>Min Trade Size Rules</h3>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Min Shares</label>
          <input
            type="number"
            placeholder="e.g., 1"
            value={data.minShares || ''}
            onChange={(e) => handleChange('minShares', e.target.value)}
          />
        </div>
        <div className="form-group">
          <label>Min Notional ($)</label>
          <input
            type="number"
            placeholder="e.g., 100"
            value={data.minNotional || ''}
            onChange={(e) => handleChange('minNotional', e.target.value)}
          />
        </div>
      </div>
    </div>
  )
}

export default RebalancingRules


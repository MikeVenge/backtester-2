import React from 'react'
import './FormSection.css'

function TradingExecution({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    onChange({
      ...data,
      [field]: value
    })
  }

  return (
    <div className="form-section">
      <h2>Trading & Execution Assumptions</h2>
      
      <div className="form-section-divider">
        <h3>Order Type & Execution Timing</h3>
      </div>

      <div className="form-group">
        <label>Entry Timing</label>
        <select
          value={data.entryTiming || ''}
          onChange={(e) => handleChange('entryTiming', e.target.value)}
        >
          <option value="">Select timing</option>
          <option value="next-bar-open">Next Bar Open</option>
          <option value="same-bar-close">Same Bar Close</option>
          <option value="midpoint">Midpoint</option>
          <option value="vwap">VWAP</option>
        </select>
      </div>

      <div className="form-group">
        <label>Order Type</label>
        <select
          value={data.orderType || ''}
          onChange={(e) => handleChange('orderType', e.target.value)}
        >
          <option value="">Select type</option>
          <option value="market">Market Orders</option>
          <option value="limit">Limit Orders</option>
        </select>
      </div>

      {data.orderType === 'limit' && (
        <div className="form-group">
          <label>Limit Order Logic</label>
          <textarea
            rows="3"
            placeholder="Describe limit order logic"
            value={data.limitOrderLogic || ''}
            onChange={(e) => handleChange('limitOrderLogic', e.target.value)}
          />
        </div>
      )}

      <div className="form-section-divider">
        <h3>Transaction Cost Model</h3>
      </div>

      <div className="form-group">
        <label>Commission Type</label>
        <select
          value={data.commissionType || ''}
          onChange={(e) => handleChange('commissionType', e.target.value)}
        >
          <option value="">Select type</option>
          <option value="per-trade">Per Trade</option>
          <option value="per-share">Per Share</option>
          <option value="per-contract">Per Contract</option>
        </select>
      </div>

      <div className="form-group">
        <label>Commission Amount</label>
        <input
          type="number"
          step="0.01"
          placeholder="e.g., 1.00"
          value={data.commissionAmount || ''}
          onChange={(e) => handleChange('commissionAmount', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Exchange Fees (%)</label>
        <input
          type="number"
          step="0.001"
          placeholder="e.g., 0.1"
          value={data.exchangeFees || ''}
          onChange={(e) => handleChange('exchangeFees', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Bid-Ask Spread / Slippage (%)</label>
        <input
          type="number"
          step="0.001"
          placeholder="e.g., 0.02"
          value={data.slippage || ''}
          onChange={(e) => handleChange('slippage', e.target.value)}
        />
        <small>Assumption per trade (e.g., 0.02%)</small>
      </div>

      <div className="form-section-divider">
        <h3>Trading Calendar & Availability</h3>
      </div>

      <div className="form-group">
        <label>Trading Days</label>
        <div className="checkbox-group">
          {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(day => (
            <label key={day} className="checkbox-label">
              <input
                type="checkbox"
                checked={data.tradingDays?.includes(day) || (day !== 'Saturday' && day !== 'Sunday')}
                onChange={(e) => {
                  const days = data.tradingDays || ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                  if (e.target.checked) {
                    handleChange('tradingDays', [...days, day])
                  } else {
                    handleChange('tradingDays', days.filter(d => d !== day))
                  }
                }}
              />
              {day}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Handle Missing Data</label>
        <select
          value={data.handleMissingData || ''}
          onChange={(e) => handleChange('handleMissingData', e.target.value)}
        >
          <option value="">Select method</option>
          <option value="skip">Skip Bar</option>
          <option value="forward-fill">Forward Fill</option>
          <option value="interpolate">Interpolate</option>
        </select>
      </div>

      <div className="form-section-divider">
        <h3>Short Selling Rules</h3>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={data.shortSellingAllowed || false}
            onChange={(e) => handleChange('shortSellingAllowed', e.target.checked)}
          />
          Allow Short Selling
        </label>
      </div>

      {data.shortSellingAllowed && (
        <>
          <div className="form-group">
            <label>Borrow Cost (%)</label>
            <input
              type="number"
              step="0.01"
              placeholder="e.g., 2.5"
              value={data.borrowCost || ''}
              onChange={(e) => handleChange('borrowCost', e.target.value)}
            />
            <small>Annual borrow cost percentage</small>
          </div>
          <div className="form-group">
            <label>Short Selling Constraints</label>
            <textarea
              rows="2"
              placeholder="Describe any constraints"
              value={data.shortConstraints || ''}
              onChange={(e) => handleChange('shortConstraints', e.target.value)}
            />
          </div>
        </>
      )}
    </div>
  )
}

export default TradingExecution


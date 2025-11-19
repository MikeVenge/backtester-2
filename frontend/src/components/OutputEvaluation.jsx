import React from 'react'
import './FormSection.css'

function OutputEvaluation({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    onChange({
      ...data,
      [field]: value
    })
  }

  return (
    <div className="form-section">
      <h2>Output & Evaluation Preferences</h2>
      
      <div className="form-section-divider">
        <h3>Performance Metrics</h3>
      </div>

      <div className="form-group">
        <label>Basic Metrics</label>
        <div className="checkbox-group">
          {['Total Return', 'CAGR', 'Max Drawdown', 'Volatility'].map(metric => (
            <label key={metric} className="checkbox-label">
              <input
                type="checkbox"
                checked={data.basicMetrics?.includes(metric) || true}
                onChange={(e) => {
                  const metrics = data.basicMetrics || ['Total Return', 'CAGR', 'Max Drawdown', 'Volatility']
                  if (e.target.checked) {
                    handleChange('basicMetrics', [...metrics, metric])
                  } else {
                    handleChange('basicMetrics', metrics.filter(m => m !== metric))
                  }
                }}
              />
              {metric}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Ratio Metrics</label>
        <div className="checkbox-group">
          {['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio'].map(ratio => (
            <label key={ratio} className="checkbox-label">
              <input
                type="checkbox"
                checked={data.ratioMetrics?.includes(ratio) || false}
                onChange={(e) => {
                  const ratios = data.ratioMetrics || []
                  if (e.target.checked) {
                    handleChange('ratioMetrics', [...ratios, ratio])
                  } else {
                    handleChange('ratioMetrics', ratios.filter(r => r !== ratio))
                  }
                }}
              />
              {ratio}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Trade Statistics</label>
        <div className="checkbox-group">
          {['Win Rate', 'Average Win/Loss', 'Profit Factor', 'Average Holding Period'].map(stat => (
            <label key={stat} className="checkbox-label">
              <input
                type="checkbox"
                checked={data.tradeStats?.includes(stat) || false}
                onChange={(e) => {
                  const stats = data.tradeStats || []
                  if (e.target.checked) {
                    handleChange('tradeStats', [...stats, stat])
                  } else {
                    handleChange('tradeStats', stats.filter(s => s !== stat))
                  }
                }}
              />
              {stat}
            </label>
          ))}
        </div>
      </div>

      <div className="form-section-divider">
        <h3>Reporting Style</h3>
      </div>

      <div className="form-group">
        <label>Output Formats</label>
        <div className="checkbox-group">
          {['Equity Curve', 'Monthly/Annual Returns Table', 'Distribution of Drawdowns', 'Trade Log'].map(format => (
            <label key={format} className="checkbox-label">
              <input
                type="checkbox"
                checked={data.outputFormats?.includes(format) || false}
                onChange={(e) => {
                  const formats = data.outputFormats || []
                  if (e.target.checked) {
                    handleChange('outputFormats', [...formats, format])
                  } else {
                    handleChange('outputFormats', formats.filter(f => f !== format))
                  }
                }}
              />
              {format}
            </label>
          ))}
        </div>
      </div>

      <div className="form-section-divider">
        <h3>Benchmark Comparison</h3>
      </div>

      <div className="form-group">
        <label>Benchmark Symbol</label>
        <input
          type="text"
          placeholder="e.g., SPY"
          value={data.benchmarkSymbol || ''}
          onChange={(e) => handleChange('benchmarkSymbol', e.target.value)}
        />
        <small>What benchmark to compare against</small>
      </div>

      <div className="form-group">
        <label>Benchmark Metrics</label>
        <div className="checkbox-group">
          {['Alpha', 'Beta', 'Tracking Error'].map(metric => (
            <label key={metric} className="checkbox-label">
              <input
                type="checkbox"
                checked={data.benchmarkMetrics?.includes(metric) || false}
                onChange={(e) => {
                  const metrics = data.benchmarkMetrics || []
                  if (e.target.checked) {
                    handleChange('benchmarkMetrics', [...metrics, metric])
                  } else {
                    handleChange('benchmarkMetrics', metrics.filter(m => m !== metric))
                  }
                }}
              />
              {metric}
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}

export default OutputEvaluation


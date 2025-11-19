import React from 'react'
import './FormSection.css'

function ImplementationDetails({ data = {}, onChange }) {
  const handleChange = (field, value) => {
    onChange({
      ...data,
      [field]: value
    })
  }

  return (
    <div className="form-section">
      <h2>Practical Implementation Details</h2>
      
      <div className="form-section-divider">
        <h3>Programming Environment</h3>
      </div>

      <div className="form-group">
        <label>Programming Language / Environment</label>
        <select
          value={data.programmingEnv || ''}
          onChange={(e) => handleChange('programmingEnv', e.target.value)}
        >
          <option value="">Select environment</option>
          <option value="python">Python</option>
          <option value="excel">Excel</option>
          <option value="javascript">JavaScript/Node.js</option>
          <option value="r">R</option>
          <option value="matlab">MATLAB</option>
          <option value="other">Other</option>
        </select>
      </div>

      {data.programmingEnv === 'other' && (
        <div className="form-group">
          <label>Specify Environment</label>
          <input
            type="text"
            placeholder="e.g., C++, Java"
            value={data.otherEnv || ''}
            onChange={(e) => handleChange('otherEnv', e.target.value)}
          />
        </div>
      )}

      <div className="form-section-divider">
        <h3>Data Format</h3>
      </div>

      <div className="form-group">
        <label>Data Source Format</label>
        <select
          value={data.dataFormat || ''}
          onChange={(e) => handleChange('dataFormat', e.target.value)}
        >
          <option value="">Select format</option>
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
          <option value="database">Database</option>
          <option value="api">API Source</option>
          <option value="parquet">Parquet</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div className="form-group">
        <label>Column Names</label>
        <textarea
          rows="3"
          placeholder="e.g., Date, Open, High, Low, Close, Volume"
          value={data.columnNames || ''}
          onChange={(e) => handleChange('columnNames', e.target.value)}
        />
        <small>Specify expected column names</small>
      </div>

      <div className="form-group">
        <label>Date Format</label>
        <input
          type="text"
          placeholder="e.g., YYYY-MM-DD, MM/DD/YYYY"
          value={data.dateFormat || ''}
          onChange={(e) => handleChange('dateFormat', e.target.value)}
        />
      </div>

      {data.dataFormat === 'database' && (
        <>
          <div className="form-group">
            <label>Database Type</label>
            <select
              value={data.databaseType || ''}
              onChange={(e) => handleChange('databaseType', e.target.value)}
            >
              <option value="">Select database</option>
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
              <option value="mongodb">MongoDB</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="form-group">
            <label>Table Name</label>
            <input
              type="text"
              placeholder="e.g., price_data"
              value={data.tableName || ''}
              onChange={(e) => handleChange('tableName', e.target.value)}
            />
          </div>
        </>
      )}

      {data.dataFormat === 'api' && (
        <>
          <div className="form-group">
            <label>API Provider</label>
            <input
              type="text"
              placeholder="e.g., Alpha Vantage, Yahoo Finance"
              value={data.apiProvider || ''}
              onChange={(e) => handleChange('apiProvider', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>API Endpoint</label>
            <input
              type="text"
              placeholder="e.g., https://api.example.com/data"
              value={data.apiEndpoint || ''}
              onChange={(e) => handleChange('apiEndpoint', e.target.value)}
            />
          </div>
        </>
      )}
    </div>
  )
}

export default ImplementationDetails


import React, { useState } from 'react'
import Tabs from './components/Tabs'
import MarketData from './components/MarketData'
import StrategyDefinition from './components/StrategyDefinition'
import PortfolioRiskSettings from './components/PortfolioRiskSettings'
import TradingExecution from './components/TradingExecution'
import MTMSettings from './components/MTMSettings'
import RebalancingRules from './components/RebalancingRules'
import OutputEvaluation from './components/OutputEvaluation'
import ImplementationDetails from './components/ImplementationDetails'
import ConfigurationManager from './components/ConfigurationManager'
import './App.css'

const TABS = [
  { id: 'market-data', label: 'Market Data' },
  { id: 'strategy', label: 'Strategy Definition' },
  { id: 'portfolio-risk', label: 'Portfolio & Risk' },
  { id: 'trading-execution', label: 'Trading & Execution' },
  { id: 'mtm', label: 'Mark-to-Market' },
  { id: 'rebalancing', label: 'Rebalancing Rules' },
  { id: 'output', label: 'Output & Evaluation' },
  { id: 'implementation', label: 'Implementation' },
]

function App() {
  const [activeTab, setActiveTab] = useState('market-data')
  const [formData, setFormData] = useState({})
  const [currentConfigName, setCurrentConfigName] = useState(null)

  const updateFormData = (section, data) => {
    setFormData(prev => ({
      ...prev,
      [section]: data
    }))
  }

  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
  }

  const handleLoadConfiguration = (loadedData, configName = null) => {
    setFormData(loadedData)
    setCurrentConfigName(configName)
  }

  const handleSaveConfiguration = () => {
    // This is handled by ConfigurationManager component
    // but we expose it here for potential future use
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'market-data':
        return <MarketData data={formData['market-data']} onChange={(data) => updateFormData('market-data', data)} />
      case 'strategy':
        return <StrategyDefinition data={formData['strategy']} onChange={(data) => updateFormData('strategy', data)} />
      case 'portfolio-risk':
        return <PortfolioRiskSettings data={formData['portfolio-risk']} onChange={(data) => updateFormData('portfolio-risk', data)} />
      case 'trading-execution':
        return <TradingExecution data={formData['trading-execution']} onChange={(data) => updateFormData('trading-execution', data)} />
      case 'mtm':
        return <MTMSettings data={formData['mtm']} onChange={(data) => updateFormData('mtm', data)} />
      case 'rebalancing':
        return <RebalancingRules data={formData['rebalancing']} onChange={(data) => updateFormData('rebalancing', data)} />
      case 'output':
        return <OutputEvaluation data={formData['output']} onChange={(data) => updateFormData('output', data)} />
      case 'implementation':
        return <ImplementationDetails data={formData['implementation']} onChange={(data) => updateFormData('implementation', data)} />
      default:
        return null
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Backtester Configuration</h1>
        <p>Configure your backtesting parameters</p>
      </header>
      <div className="app-container">
        <ConfigurationManager 
          formData={formData}
          currentConfigName={currentConfigName}
          onLoadConfiguration={handleLoadConfiguration}
          onSaveConfiguration={handleSaveConfiguration}
          onConfigNameChange={setCurrentConfigName}
        />
        <Tabs tabs={TABS} activeTab={activeTab} onTabChange={handleTabChange} />
        <div className="tab-content">
          {renderTabContent()}
        </div>
      </div>
    </div>
  )
}

export default App


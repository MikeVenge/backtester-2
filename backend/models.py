from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import date

# --- 1. Market Data ---
class MarketData(BaseModel):
    tickers: Optional[str] = None
    fields: List[str] = []
    frequency: Optional[str] = None
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    includeDividends: bool = False
    includeSplits: bool = False
    includeDelistings: bool = False
    benchmark: Optional[str] = None

# --- 2. Strategy Definition ---
class StrategyDefinition(BaseModel):
    entryLogic: Optional[str] = None
    entryPromptType: str = "url"  # "url", "string", or "finchat-slug"
    entryFinChatUrl: Optional[str] = None
    entryFinChatPrompt: Optional[str] = None
    entryFinChatSlug: Optional[str] = None  # FinChat COT slug for entry logic
    
    exitLogic: Optional[str] = None
    exitPromptType: str = "url"   # "url", "string", or "finchat-slug"
    exitFinChatUrl: Optional[str] = None
    exitFinChatPrompt: Optional[str] = None
    exitFinChatSlug: Optional[str] = None  # FinChat COT slug for exit logic
    
    takeProfit: Optional[float] = None
    stopLoss: Optional[float] = None
    timeBasedExit: Optional[int] = None
    
    # FinChat exit COT thresholds
    upsideThreshold: Optional[float] = None  # Upside sell threshold percentage
    downsideThreshold: Optional[float] = None  # Downside sell threshold percentage
    
    positionSizingMethod: Optional[str] = None
    fixedDollarAmount: Optional[float] = None
    portfolioPercent: Optional[float] = None
    riskPercent: Optional[float] = None
    maxPositions: Optional[int] = None
    
    eligibleSymbols: Optional[str] = None
    rankingLogic: Optional[str] = None

# --- 3. Portfolio & Risk Settings ---
class PortfolioRiskSettings(BaseModel):
    initialCapital: Optional[float] = None
    leverageAllowed: bool = False
    maxLeverage: Optional[float] = None
    maxSingleAssetPercent: Optional[float] = None
    maxSectorPercent: Optional[float] = None
    maxNetExposure: Optional[float] = None
    stopLossType: Optional[str] = None
    takeProfitRules: Optional[str] = None
    useTrailingStops: bool = False
    trailingStopDistance: Optional[float] = None
    maxDailyDrawdown: Optional[float] = None
    maxWeeklyDrawdown: Optional[float] = None

# --- 4. Trading & Execution Assumptions ---
class TradingExecution(BaseModel):
    entryTiming: Optional[str] = None
    orderType: Optional[str] = None
    limitOrderLogic: Optional[str] = None
    commissionType: Optional[str] = None
    commissionAmount: Optional[float] = None
    exchangeFees: Optional[float] = None
    slippage: Optional[float] = None
    tradingDays: List[str] = []
    handleMissingData: Optional[str] = None
    shortSellingAllowed: bool = False
    borrowCost: Optional[float] = None
    shortConstraints: Optional[str] = None

# --- 5. Mark-to-Market (MTM) Settings ---
class MTMSettings(BaseModel):
    mtmFrequency: Optional[str] = None
    mtmPrice: Optional[str] = None
    customMTMRule: Optional[str] = None
    baseCurrency: Optional[str] = None
    fxFrequency: Optional[str] = None
    mtmFXSeparately: bool = False
    adjustForSplitsDividends: bool = False
    bookDividendCashflows: bool = False

# --- 6. Rebalancing Rules ---
class RebalancingRules(BaseModel):
    rebalancingType: Optional[str] = None
    calendarFrequency: Optional[str] = None
    specificDay: Optional[str] = None
    driftThreshold: Optional[float] = None
    signalDescription: Optional[str] = None
    hybridCheckFrequency: Optional[str] = None
    hybridDriftThreshold: Optional[float] = None
    addRules: Optional[str] = None
    dropDelisted: bool = False
    dropBelowThresholds: bool = False
    exitIneligible: bool = False
    rebalancingMethod: Optional[str] = None
    maxTurnover: Optional[float] = None
    minShares: Optional[float] = None
    minNotional: Optional[float] = None

# --- 7. Output & Evaluation Preferences ---
class OutputEvaluation(BaseModel):
    basicMetrics: List[str] = []
    ratioMetrics: List[str] = []
    tradeStats: List[str] = []
    outputFormats: List[str] = []
    benchmarkSymbol: Optional[str] = None
    benchmarkMetrics: List[str] = []

# --- 8. Implementation Details ---
class ImplementationDetails(BaseModel):
    programmingEnv: Optional[str] = None
    otherEnv: Optional[str] = None
    dataFormat: Optional[str] = None
    columnNames: Optional[str] = None
    dateFormat: Optional[str] = None
    databaseType: Optional[str] = None
    tableName: Optional[str] = None
    apiProvider: Optional[str] = None
    apiEndpoint: Optional[str] = None

# --- Root Configuration Object ---
class BacktestConfiguration(BaseModel):
    marketData: Optional[MarketData] = None
    strategy: Optional[StrategyDefinition] = None
    portfolioRisk: Optional[PortfolioRiskSettings] = None
    tradingExecution: Optional[TradingExecution] = None
    mtm: Optional[MTMSettings] = None
    rebalancing: Optional[RebalancingRules] = None
    output: Optional[OutputEvaluation] = None
    implementation: Optional[ImplementationDetails] = None

class BacktestRequest(BaseModel):
    name: str
    data: BacktestConfiguration
    timestamp: Optional[str] = None


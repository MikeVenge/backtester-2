# Backtester API Guide

## Base URL
```
http://localhost:8000
```

## Prerequisites
1. Run the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
2. Provide an AlphaVantage key:
   ```bash
   export ALPHAVANTAGE_API_KEY="YOUR_KEY"
   ```

## Endpoints

### 1. `GET /health`
Quick health/status check.
```json
{
  "status": "healthy",
  "timestamp": "2025-05-01T12:34:56.789012",
  "active_backtests": 0
}
```

### 2. `POST /run_backtest`
Submit a backtest job.

**Request Body:**
```json
{
  "name": "My Backtest",
  "timestamp": "2025-05-01T12:00:00Z",  // Optional
  "data": {
    "marketData": {
      "tickers": "IBM,AAPL,MSFT",  // Comma-separated ticker symbols
      "fields": ["open", "high", "low", "close", "volume"],  // OHLCV fields to fetch
      "frequency": "daily",  // Options: "daily", "weekly", "monthly", "1min", "5min", "15min", "30min", "60min"
      "startDate": "2024-05-01",  // YYYY-MM-DD format
      "endDate": "2025-05-01",  // YYYY-MM-DD format
      "includeDividends": true,  // Include dividend data
      "includeSplits": true,  // Include stock split data
      "includeDelistings": false,  // Track delisted stocks
      "benchmark": "SPY"  // Optional benchmark ticker
    },
    "strategy": {
      "entryLogic": "Buy when 5-day MA crosses above 20-day MA",  // Entry signal description
      "entryPromptType": "string",  // "url" or "string"
      "entryFinChatUrl": null,  // URL to FinChat prompt (if entryPromptType="url")
      "entryFinChatPrompt": "Buy when 5-day MA crosses above 20-day MA",  // Entry logic string
      "exitLogic": "Sell when 5-day MA crosses below 20-day MA",  // Exit signal description
      "exitPromptType": "string",  // "url" or "string"
      "exitFinChatUrl": null,  // URL to FinChat prompt (if exitPromptType="url")
      "exitFinChatPrompt": "Sell when 5-day MA crosses below 20-day MA",  // Exit logic string
      "takeProfit": 10.0,  // Take-profit percentage (e.g., 10 = 10%)
      "stopLoss": 5.0,  // Stop-loss percentage (e.g., 5 = 5%)
      "timeBasedExit": 30,  // Exit after N days
      "positionSizingMethod": "fixed-dollar",  // Options: "fixed-dollar", "portfolio-percent", "risk-based"
      "fixedDollarAmount": 10000.0,  // Dollar amount per position (if positionSizingMethod="fixed-dollar")
      "portfolioPercent": 10.0,  // Percentage of portfolio per position (if positionSizingMethod="portfolio-percent")
      "riskPercent": 2.0,  // Risk percentage for position sizing (if positionSizingMethod="risk-based")
      "maxPositions": 10,  // Maximum concurrent positions
      "eligibleSymbols": "All tickers in universe",  // Description of eligible universe
      "rankingLogic": "Rank by momentum"  // Ranking/filtering logic for signals
    },
    "portfolioRisk": {
      "initialCapital": 1000000.0,  // Starting capital in dollars
      "leverageAllowed": false,  // Whether leverage is permitted
      "maxLeverage": 1.0,  // Maximum leverage multiplier (e.g., 2.0 = 2x)
      "maxSingleAssetPercent": 20.0,  // Maximum % in one position
      "maxSectorPercent": 50.0,  // Maximum % in one sector
      "maxNetExposure": 100.0,  // Maximum net long/short exposure %
      "stopLossType": "fixed-percent",  // Options: "fixed-percent", "volatility-based", "dollar-based"
      "takeProfitRules": "Scale out at 5% and 10%",  // Description of take-profit logic
      "useTrailingStops": true,  // Whether to use trailing stops
      "trailingStopDistance": 3.0,  // Trailing stop distance percentage
      "maxDailyDrawdown": 5.0,  // Maximum daily drawdown % (halt trading if exceeded)
      "maxWeeklyDrawdown": 10.0  // Maximum weekly drawdown % (halt trading if exceeded)
    },
    "tradingExecution": {
      "entryTiming": "next-bar-open",  // Options: "next-bar-open", "same-bar-close", "midpoint", "vwap"
      "orderType": "market",  // Options: "market", "limit"
      "limitOrderLogic": "Limit at 0.5% below current price",  // Description (if orderType="limit")
      "commissionType": "per-trade",  // Options: "per-trade", "per-share", "per-contract"
      "commissionAmount": 1.0,  // Commission amount
      "exchangeFees": 0.01,  // Exchange fees as percentage
      "slippage": 0.05,  // Slippage assumption as percentage
      "tradingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],  // Days when trading is allowed
      "handleMissingData": "forward-fill",  // Options: "skip", "forward-fill", "interpolate"
      "shortSellingAllowed": false,  // Whether short selling is permitted
      "borrowCost": 0.5,  // Borrow cost % for short positions (annual)
      "shortConstraints": "No hard-to-borrow stocks"  // Description of short constraints
    },
    "mtm": {
      "mtmFrequency": "daily",  // Options: "every-bar", "daily", "weekly", "monthly"
      "mtmPrice": "close",  // Options: "close", "vwap", "mid", "last", "custom"
      "customMTMRule": null,  // Custom MTM rule (if mtmPrice="custom")
      "baseCurrency": "USD",  // Base currency code
      "fxFrequency": "daily",  // Options: "daily", "intraday"
      "mtmFXSeparately": false,  // Whether to MTM FX separately
      "adjustForSplitsDividends": true,  // Adjust historical prices for splits/dividends
      "bookDividendCashflows": true  // Book dividends explicitly to cash
    },
    "rebalancing": {
      "rebalancingType": "calendar-based",  // Options: "calendar-based", "threshold-based", "signal-based", "hybrid"
      "calendarFrequency": "monthly",  // Options: "daily", "weekly", "monthly", "quarterly" (if calendar-based)
      "specificDay": "First trading day of month",  // Specific day description (if calendar-based)
      "driftThreshold": 5.0,  // Weight drift % (if threshold-based)
      "signalDescription": "Rebalance when new signals generated",  // Signal description (if signal-based)
      "hybridCheckFrequency": "weekly",  // Check frequency (if hybrid)
      "hybridDriftThreshold": 3.0,  // Drift threshold % (if hybrid)
      "addRules": "Add new tickers meeting liquidity criteria",  // Rules for adding assets
      "dropDelisted": true,  // Drop delisted assets
      "dropBelowThresholds": false,  // Drop assets below thresholds
      "exitIneligible": true,  // Exit positions leaving universe
      "rebalancingMethod": "full",  // Options: "full", "partial", "buy-only", "turnover-limited"
      "maxTurnover": 20.0,  // Max turnover % per rebalance (if turnover-limited)
      "minShares": 1.0,  // Minimum shares per trade
      "minNotional": 100.0  // Minimum notional value per trade
    },
    "output": {
      "basicMetrics": ["Total Return", "CAGR", "Max Drawdown", "Volatility"],  // Basic metrics to calculate
      "ratioMetrics": ["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio"],  // Ratio metrics to calculate
      "tradeStats": ["Win Rate", "Average Win/Loss", "Profit Factor", "Average Holding Period"],  // Trade statistics
      "outputFormats": ["Equity Curve", "Monthly/Annual Returns Table", "Distribution of Drawdowns", "Trade Log"],  // Output formats
      "benchmarkSymbol": "SPY",  // Benchmark ticker for comparison
      "benchmarkMetrics": ["Alpha", "Beta", "Tracking Error"]  // Benchmark comparison metrics
    },
    "implementation": {
      "programmingEnv": "python",  // Options: "python", "excel", "other"
      "otherEnv": null,  // Custom environment (if programmingEnv="other")
      "dataFormat": "json",  // Options: "csv", "json", "database", "api", "parquet", "other"
      "columnNames": "timestamp,open,high,low,close,volume",  // Expected column names
      "dateFormat": "YYYY-MM-DD",  // Date format string
      "databaseType": null,  // Database type (if dataFormat="database")
      "tableName": null,  // Table name (if dataFormat="database")
      "apiProvider": null,  // API provider name (if dataFormat="api")
      "apiEndpoint": null  // API endpoint (if dataFormat="api")
    }
  }
}
```
Response:
```json
{
  "status": "queued",
  "job_id": "UUID",
  "message": "Backtest 'My Backtest' has been queued for execution",
  "config_summary": {
    "name": "My Backtest",
    "tickers": "IBM",
    "start_date": "2024-05-01",
    "end_date": "2025-05-01",
    "initial_capital": 1000000
  }
}
```

### 3. `GET /backtest_status/{job_id}`
```json
{
  "job_id": "UUID",
  "status": "completed",
  "summary": {
    "total_return": 0.74,
    "cagr": 0.74,
    ...
  }
}
```
Status values: `queued`, `running`, `completed`, `failed`.

### 4. `GET /backtest_results/{job_id}`
Returns full results (summary metrics, trade list, equity curve, benchmark comparison).  
If still running: HTTP 202.

### 5. `GET /list_backtests`
Lists all known jobs.
```json
{
  "jobs": [
    {
      "job_id": "UUID",
      "status": "completed",
      "summary": {
        "total_return": 0.74,
        "sharpe_ratio": -2.01,
        "num_trades": 41
      }
    }
  ],
  "total": 1
}
```

### 6. `DELETE /backtest_results/{job_id}`
Removes stored results/status.
```json
{
  "status": "success",
  "message": "Backtest UUID deleted"
}
```

**Response:**
```json
{
  "status": "queued",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Backtest 'My Backtest' has been queued for execution",
  "config_summary": {
    "name": "My Backtest",
    "tickers": "IBM,AAPL,MSFT",
    "start_date": "2024-05-01",
    "end_date": "2025-05-01",
    "initial_capital": 1000000.0
  }
}
```

**Complete Example Request:**
```json
{
  "name": "IBM Rotation Strategy",
  "data": {
    "marketData": {
      "tickers": "IBM",
      "fields": ["open", "high", "low", "close", "volume"],
      "frequency": "daily",
      "startDate": "2024-05-01",
      "endDate": "2025-05-01",
      "includeDividends": true,
      "includeSplits": true,
      "includeDelistings": false,
      "benchmark": null
    },
    "strategy": {
      "entryLogic": "Buy every 3 trading days",
      "entryPromptType": "string",
      "entryFinChatPrompt": "Buy every 3 trading days",
      "exitLogic": "Sell after 6 trading days",
      "exitPromptType": "string",
      "exitFinChatPrompt": "Sell after 6 trading days",
      "takeProfit": null,
      "stopLoss": null,
      "timeBasedExit": 6,
      "positionSizingMethod": "fixed-dollar",
      "fixedDollarAmount": 16443.0,
      "portfolioPercent": null,
      "riskPercent": null,
      "maxPositions": 100,
      "eligibleSymbols": "IBM",
      "rankingLogic": null
    },
    "portfolioRisk": {
      "initialCapital": 1000000.0,
      "leverageAllowed": false,
      "maxLeverage": 1.0,
      "maxSingleAssetPercent": 100.0,
      "maxSectorPercent": 100.0,
      "maxNetExposure": 100.0,
      "stopLossType": "fixed-percent",
      "takeProfitRules": null,
      "useTrailingStops": false,
      "trailingStopDistance": null,
      "maxDailyDrawdown": null,
      "maxWeeklyDrawdown": null
    },
    "tradingExecution": {
      "entryTiming": "same-bar-close",
      "orderType": "market",
      "limitOrderLogic": null,
      "commissionType": "per-trade",
      "commissionAmount": 1.0,
      "exchangeFees": 0.0,
      "slippage": 0.0,
      "tradingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "handleMissingData": "forward-fill",
      "shortSellingAllowed": false,
      "borrowCost": 0.0,
      "shortConstraints": null
    },
    "mtm": {
      "mtmFrequency": "daily",
      "mtmPrice": "close",
      "customMTMRule": null,
      "baseCurrency": "USD",
      "fxFrequency": "daily",
      "mtmFXSeparately": false,
      "adjustForSplitsDividends": true,
      "bookDividendCashflows": true
    },
    "rebalancing": {
      "rebalancingType": null,
      "calendarFrequency": null,
      "specificDay": null,
      "driftThreshold": null,
      "signalDescription": null,
      "hybridCheckFrequency": null,
      "hybridDriftThreshold": null,
      "addRules": null,
      "dropDelisted": false,
      "dropBelowThresholds": false,
      "exitIneligible": false,
      "rebalancingMethod": "full",
      "maxTurnover": null,
      "minShares": 1.0,
      "minNotional": 0.0
    },
    "output": {
      "basicMetrics": ["Total Return", "CAGR", "Max Drawdown", "Volatility"],
      "ratioMetrics": ["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio"],
      "tradeStats": ["Win Rate", "Average Win/Loss", "Profit Factor", "Average Holding Period"],
      "outputFormats": ["Equity Curve", "Trade Log"],
      "benchmarkSymbol": null,
      "benchmarkMetrics": []
    },
    "implementation": {
      "programmingEnv": "python",
      "otherEnv": null,
      "dataFormat": "json",
      "columnNames": "timestamp,open,high,low,close,volume",
      "dateFormat": "YYYY-MM-DD",
      "databaseType": null,
      "tableName": null,
      "apiProvider": null,
      "apiEndpoint": null
    }
  }
}
```

## Tips
- Use Swagger (`/docs`) or ReDoc (`/redoc`) for interactive schemas and testing.
- Run via `curl`:
  ```bash
  curl -X POST http://localhost:8000/run_backtest \
       -H "Content-Type: application/json" \
       -d @config.json
  ```
- All market data requests require `ALPHAVANTAGE_API_KEY` environment variable.
- Optional fields can be omitted or set to `null`.
- Date formats must be `YYYY-MM-DD` (e.g., "2024-05-01").


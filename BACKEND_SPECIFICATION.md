# Backend Specification for Backtester Engine

## Overview
This document specifies how the backend will process each configuration section from the frontend and execute the backtest. The backend will validate inputs, fetch market data, execute trading logic, and generate performance reports.

---

## 1. MARKET DATA Tab

### Inputs Received:
- `tickers` (string): Comma-separated ticker symbols
- `fields` (array): Selected OHLCV fields ['Open', 'High', 'Low', 'Close', 'Volume']
- `frequency` (string): Data frequency (tick, 1min, 5min, hourly, daily, weekly)
- `startDate` (date): Backtest start date
- `endDate` (date): Backtest end date
- `includeDividends` (boolean): Whether to include dividend data
- `includeSplits` (boolean): Whether to include stock splits
- `includeDelistings` (boolean): Whether to track delistings/mergers
- `benchmark` (string): Benchmark ticker symbol (optional)

### Backend Processing:
1. **Data Validation**:
   - Validate tickers are not empty
   - Parse comma-separated tickers into array
   - Validate startDate < endDate
   - Validate frequency is supported by data provider

2. **Data Fetching** (using AlphaVantage MCP):
   - For each ticker, fetch OHLCV data based on frequency
   - If `includeDividends=true`: Fetch dividend history via `DIVIDENDS` endpoint
   - If `includeSplits=true`: Fetch split history via `SPLITS` endpoint
   - If benchmark specified: Fetch benchmark data with same frequency/date range
   - Handle delistings by checking `LISTING_STATUS` endpoint if `includeDelistings=true`

3. **Data Processing**:
   - Align all ticker data to common timestamps
   - Apply split adjustments to historical prices if `includeSplits=true`
   - Filter data to only include selected `fields`
   - Handle missing data based on Trading & Execution settings (forward-fill, skip, etc.)

4. **Output**:
   - DataFrame with MultiIndex (timestamp, ticker) and columns for selected fields
   - Separate DataFrame for benchmark data
   - Corporate action log (dividends, splits, delistings)

---

## 2. STRATEGY DEFINITION Tab

### Inputs Received:
- `entryPromptType` (string): "url" or "string"
- `entryFinChatUrl` (string): URL to FinChat prompt (if type=url)
- `entryFinChatPrompt` (string): Entry logic string (if type=string)
- `entryLogic` (string): Synced with entryFinChatPrompt when type=string
- `exitPromptType` (string): "url" or "string"
- `exitFinChatUrl` (string): URL to FinChat prompt (if type=url)
- `exitFinChatPrompt` (string): Exit logic string (if type=string)
- `exitLogic` (string): Synced with exitFinChatPrompt when type=string
- `takeProfit` (float): Take-profit percentage
- `stopLoss` (float): Stop-loss percentage
- `timeBasedExit` (int): Time-based exit in days
- `positionSizingMethod` (string): "fixed-dollar", "portfolio-percent", "risk-based"
- `fixedDollarAmount` (float): If method=fixed-dollar
- `portfolioPercent` (float): If method=portfolio-percent
- `riskPercent` (float): If method=risk-based
- `maxPositions` (int): Max concurrent positions
- `eligibleSymbols` (string): Description of eligible universe
- `rankingLogic` (string): Ranking/filtering logic

### Backend Processing:
1. **Entry/Exit Signal Generation**:
   - If `entryPromptType=url`: Fetch prompt from FinChat URL, parse into executable logic
   - If `entryPromptType=string`: Parse `entryFinChatPrompt` as natural language or code
   - Use LLM or rule engine to convert prompts into executable signal functions
   - Generate entry_signal(data, ticker, timestamp) → boolean function
   - Generate exit_signal(data, ticker, timestamp, position) → boolean function

2. **Position Sizing Calculator**:
   - Create position_size(current_capital, signal_strength) function based on method:
     - **fixed-dollar**: Return `fixedDollarAmount / current_price`
     - **portfolio-percent**: Return `current_capital * portfolioPercent / 100 / current_price`
     - **risk-based**: Calculate position size based on `riskPercent` and stop-loss distance

3. **Exit Condition Handler**:
   - Monitor each position for:
     - Exit signal trigger (from exit logic)
     - Take-profit hit: `current_price >= entry_price * (1 + takeProfit/100)`
     - Stop-loss hit: `current_price <= entry_price * (1 - stopLoss/100)`
     - Time-based exit: `days_held >= timeBasedExit`

4. **Position Management**:
   - Track `maxPositions` constraint
   - Prevent new entries if at max positions
   - Parse `eligibleSymbols` to filter universe
   - Apply `rankingLogic` to prioritize trades if more signals than max positions

---

## 3. PORTFOLIO & RISK SETTINGS Tab

### Inputs Received:
- `initialCapital` (float): Starting capital
- `leverageAllowed` (boolean): Whether leverage is permitted
- `maxLeverage` (float): Maximum leverage multiplier
- `maxSingleAssetPercent` (float): Max % in one position
- `maxSectorPercent` (float): Max % in one sector
- `maxNetExposure` (float): Max net long/short %
- `stopLossType` (string): "fixed-percent", "volatility-based", "dollar-based"
- `takeProfitRules` (string): Description of take-profit logic
- `useTrailingStops` (boolean): Whether to use trailing stops
- `trailingStopDistance` (float): Trailing stop distance %
- `maxDailyDrawdown` (float): Max daily drawdown %
- `maxWeeklyDrawdown` (float): Max weekly drawdown %

### Backend Processing:
1. **Portfolio Initialization**:
   - Set `cash = initialCapital`
   - Initialize `positions = {}` dict to track holdings
   - Set `max_buying_power = initialCapital * maxLeverage` if leverageAllowed

2. **Position Size Validation**:
   - Before each trade, check:
     - `new_position_value / total_portfolio_value <= maxSingleAssetPercent / 100`
     - If sector data available: `sector_exposure <= maxSectorPercent / 100`
     - `net_exposure <= maxNetExposure / 100`

3. **Stop-Loss Management**:
   - Implement stop logic based on `stopLossType`:
     - **fixed-percent**: Stop at `entry_price * (1 - stopLoss/100)`
     - **volatility-based**: Stop at `entry_price - (N * ATR)` where N from config
     - **dollar-based**: Stop at `entry_price - fixed_dollar_amount`

4. **Trailing Stop Management**:
   - If `useTrailingStops=true`:
     - Track highest price since entry for each position
     - Update stop to `highest_price * (1 - trailingStopDistance/100)`
     - Trigger exit if price falls below trailing stop

5. **Drawdown Monitoring**:
   - Track peak portfolio value within day/week
   - Calculate current drawdown: `(peak - current) / peak * 100`
   - If `current_dd > maxDailyDrawdown` or `current_dd > maxWeeklyDrawdown`:
     - Halt all new trades
     - (Optional: Close all positions)

---

## 4. TRADING & EXECUTION Tab

### Inputs Received:
- `entryTiming` (string): "next-bar-open", "same-bar-close", "midpoint", "vwap"
- `orderType` (string): "market", "limit"
- `limitOrderLogic` (string): Description of limit order logic (if orderType=limit)
- `commissionType` (string): "per-trade", "per-share", "per-contract"
- `commissionAmount` (float): Commission amount
- `exchangeFees` (float): Exchange fees %
- `slippage` (float): Slippage assumption %
- `tradingDays` (array): Days of week when trading is allowed
- `handleMissingData` (string): "skip", "forward-fill", "interpolate"
- `shortSellingAllowed` (boolean): Whether shorting is permitted
- `borrowCost` (float): Borrow cost % (if shorting allowed)
- `shortConstraints` (string): Description of short constraints

### Backend Processing:
1. **Execution Price Calculation**:
   - On entry signal, determine fill price based on `entryTiming`:
     - **next-bar-open**: Use next bar's open price
     - **same-bar-close**: Use current bar's close price
     - **midpoint**: Use `(high + low) / 2` of bar
     - **vwap**: Calculate volume-weighted average price if volume data available

2. **Order Execution**:
   - **market**: Fill at calculated price
   - **limit**: Parse `limitOrderLogic` to determine limit price; only fill if market price crosses limit

3. **Transaction Costs**:
   - Calculate commission based on `commissionType`:
     - **per-trade**: Deduct `commissionAmount` per trade
     - **per-share**: Deduct `commissionAmount * shares`
     - **per-contract**: Deduct `commissionAmount * contracts`
   - Apply exchange fees: `trade_value * exchangeFees / 100`
   - Apply slippage: Adjust fill price by `±slippage%` against trader

4. **Trading Calendar**:
   - Filter data to only include bars on `tradingDays`
   - Skip execution on non-trading days

5. **Data Handling**:
   - Implement `handleMissingData` strategy:
     - **skip**: Skip bar if any data missing
     - **forward-fill**: Use last known value
     - **interpolate**: Linear interpolation

6. **Short Selling**:
   - If `shortSellingAllowed=false`: Block short position entries
   - If `shortSellingAllowed=true`:
     - Apply `borrowCost` as daily cost: `position_value * borrowCost / 100 / 365`
     - Parse `shortConstraints` for additional rules (e.g., hard-to-borrow stocks)

---

## 5. MARK-TO-MARKET (MTM) Tab

### Inputs Received:
- `mtmFrequency` (string): "every-bar", "daily", "weekly", "monthly"
- `mtmPrice` (string): "close", "vwap", "mid", "last", "custom"
- `customMTMRule` (string): Custom MTM rule (if mtmPrice=custom)
- `baseCurrency` (string): Base currency (e.g., USD)
- `fxFrequency` (string): "daily", "intraday"
- `mtmFXSeparately` (boolean): Whether to MTM FX separately
- `adjustForSplitsDividends` (boolean): Adjust historical prices
- `bookDividendCashflows` (boolean): Book dividends explicitly

### Backend Processing:
1. **MTM Frequency Handler**:
   - Determine when to recompute portfolio value:
     - **every-bar**: Recompute at every timestamp
     - **daily**: Recompute at end of each day
     - **weekly**: Recompute at end of each week
     - **monthly**: Recompute at end of each month

2. **MTM Price Selection**:
   - For each position, mark to market using:
     - **close**: Use close price
     - **vwap**: Use VWAP if available
     - **mid**: Use `(bid + ask) / 2` if bid/ask data available
     - **last**: Use last traded price
     - **custom**: Parse `customMTMRule` and apply (e.g., "mark long at bid, short at ask")

3. **Portfolio Value Calculation**:
   - `portfolio_value = cash + sum(position_qty * mtm_price for each position)`
   - Track equity curve as time series of portfolio values

4. **FX Handling**:
   - If multiple currencies involved:
     - Convert all positions to `baseCurrency`
     - Fetch FX rates at `fxFrequency`
     - If `mtmFXSeparately=true`: Track FX P&L separately from position P&L

5. **Corporate Actions**:
   - If `adjustForSplitsDividends=true`:
     - Apply split adjustments retroactively to historical prices
   - If `bookDividendCashflows=true`:
     - On ex-date: Add `dividend_per_share * shares` to cash
     - Track dividend income separately

---

## 6. REBALANCING RULES Tab

### Inputs Received:
- `rebalancingType` (string): "calendar-based", "threshold-based", "signal-based", "hybrid"
- `calendarFrequency` (string): "daily", "weekly", "monthly", "quarterly" (if calendar-based)
- `specificDay` (string): Specific day description (if calendar-based)
- `driftThreshold` (float): Weight drift % (if threshold-based)
- `signalDescription` (string): Signal description (if signal-based)
- `hybridCheckFrequency` (string): Check frequency (if hybrid)
- `hybridDriftThreshold` (float): Drift threshold % (if hybrid)
- `addRules` (string): Rules for adding assets
- `dropDelisted` (boolean): Drop delisted assets
- `dropBelowThresholds` (boolean): Drop assets below thresholds
- `exitIneligible` (boolean): Exit positions leaving universe
- `rebalancingMethod` (string): "full", "partial", "buy-only", "turnover-limited"
- `maxTurnover` (float): Max turnover % per rebalance (if turnover-limited)
- `minShares` (float): Min shares per trade
- `minNotional` (float): Min notional value per trade

### Backend Processing:
1. **Rebalancing Trigger**:
   - Determine when to rebalance based on `rebalancingType`:
     - **calendar-based**: Rebalance at `calendarFrequency` on `specificDay`
     - **threshold-based**: Check if any position drifts > `driftThreshold%` from target weight
     - **signal-based**: Rebalance when new signals generated (parse `signalDescription`)
     - **hybrid**: Check at `hybridCheckFrequency`; rebalance if drift > `hybridDriftThreshold%` OR signal changes

2. **Universe Management**:
   - Parse `addRules` to determine when to add new tickers
   - Handle removals:
     - If `dropDelisted=true`: Remove delisted tickers from universe
     - If `dropBelowThresholds=true`: Remove tickers failing liquidity/price tests
     - If `exitIneligible=true`: Close positions in tickers leaving eligible universe

3. **Rebalancing Execution**:
   - Calculate target weights for each position
   - Based on `rebalancingMethod`:
     - **full**: Trade from current weights to target weights
     - **partial**: Only trade to reduce largest deviations
     - **buy-only**: Only buy, never sell
     - **turnover-limited**: Limit total trades to `maxTurnover%` of portfolio

4. **Trade Size Filtering**:
   - Ignore trades where:
     - `shares < minShares`
     - `shares * price < minNotional`

---

## 7. OUTPUT & EVALUATION Tab

### Inputs Received:
- `basicMetrics` (array): ['Total Return', 'CAGR', 'Max Drawdown', 'Volatility']
- `ratioMetrics` (array): ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio']
- `tradeStats` (array): ['Win Rate', 'Average Win/Loss', 'Profit Factor', 'Average Holding Period']
- `outputFormats` (array): ['Equity Curve', 'Monthly/Annual Returns Table', 'Distribution of Drawdowns', 'Trade Log']
- `benchmarkSymbol` (string): Benchmark ticker
- `benchmarkMetrics` (array): ['Alpha', 'Beta', 'Tracking Error']

### Backend Processing:
1. **Performance Metrics Calculation**:
   - For each selected basic metric:
     - **Total Return**: `(final_value - initial_capital) / initial_capital * 100`
     - **CAGR**: `((final_value / initial_capital) ^ (1 / years)) - 1`
     - **Max Drawdown**: Maximum peak-to-trough decline
     - **Volatility**: Standard deviation of returns (annualized)

2. **Ratio Metrics**:
   - For each selected ratio:
     - **Sharpe Ratio**: `(mean_return - risk_free_rate) / std_return`
     - **Sortino Ratio**: `(mean_return - risk_free_rate) / downside_std`
     - **Calmar Ratio**: `CAGR / max_drawdown`

3. **Trade Statistics**:
   - Analyze trade log to calculate:
     - **Win Rate**: `winning_trades / total_trades * 100`
     - **Average Win/Loss**: `avg_winning_trade / avg_losing_trade`
     - **Profit Factor**: `gross_profit / gross_loss`
     - **Average Holding Period**: Mean duration of closed positions

4. **Output Generation**:
   - For each selected format:
     - **Equity Curve**: Time series plot of portfolio value
     - **Monthly/Annual Returns Table**: Returns aggregated by period
     - **Distribution of Drawdowns**: Histogram or distribution of drawdown periods
     - **Trade Log**: CSV/JSON of all trades with entry/exit prices, P&L, etc.

5. **Benchmark Comparison**:
   - Fetch `benchmarkSymbol` data (already loaded in Market Data step)
   - Calculate:
     - **Alpha**: Excess return vs benchmark
     - **Beta**: Correlation with benchmark
     - **Tracking Error**: Std deviation of (portfolio_return - benchmark_return)

---

## 8. IMPLEMENTATION DETAILS Tab

### Inputs Received:
- `programmingEnv` (string): Programming environment (python, excel, etc.)
- `otherEnv` (string): Custom environment (if programmingEnv=other)
- `dataFormat` (string): "csv", "json", "database", "api", "parquet", "other"
- `columnNames` (string): Expected column names
- `dateFormat` (string): Date format string
- `databaseType` (string): Database type (if dataFormat=database)
- `tableName` (string): Table name (if dataFormat=database)
- `apiProvider` (string): API provider name (if dataFormat=api)
- `apiEndpoint` (string): API endpoint (if dataFormat=api)

### Backend Processing:
1. **Data Source Configuration**:
   - This tab is metadata for the user's preferred implementation
   - Backend uses this to determine how to:
     - Format output data (`dataFormat`)
     - Parse custom data sources if user provides data
     - Map column names from user data to internal format

2. **Data Loading** (if user uploads custom data):
   - Parse data based on `dataFormat`:
     - **csv/json**: Load using pandas with `dateFormat` and `columnNames`
     - **database**: Connect to `databaseType`, query `tableName`
     - **api**: Call `apiEndpoint` from `apiProvider`
   - Map user column names to standard OHLCV format

3. **Output Formatting**:
   - Export results in format matching `dataFormat`:
     - **csv**: Export trade log and metrics as CSV
     - **json**: Export as JSON objects
     - **database**: Write results back to database
     - **api**: POST results to API endpoint

---

## Backend Execution Flow

### Phase 1: Configuration Validation
1. Receive configuration from frontend
2. Validate all required fields present
3. Validate data types and ranges
4. Return validation errors if any

### Phase 2: Data Acquisition
1. Parse tickers and date range from Market Data
2. Fetch OHLCV data from AlphaVantage MCP
3. Fetch corporate actions if requested
4. Fetch benchmark data if specified
5. Align and clean data

### Phase 3: Strategy Initialization
1. Parse entry/exit logic into executable functions
2. Initialize position sizing calculator
3. Set up portfolio with initial capital
4. Initialize risk management rules

### Phase 4: Backtest Execution Loop
```python
for timestamp in date_range:
    # 1. Mark-to-Market (if MTM frequency hit)
    update_portfolio_value(timestamp)
    
    # 2. Check Drawdown Limits
    if exceeds_drawdown_limits():
        halt_trading()
    
    # 3. Check Rebalancing
    if should_rebalance(timestamp):
        rebalance_portfolio(timestamp)
    
    # 4. Check Exit Signals for existing positions
    for position in portfolio.positions:
        if exit_signal(position, timestamp):
            close_position(position, timestamp)
    
    # 5. Check Entry Signals for new positions
    if len(portfolio.positions) < maxPositions:
        for ticker in eligible_universe:
            if entry_signal(ticker, timestamp):
                open_position(ticker, timestamp)
```

### Phase 5: Results Generation
1. Calculate all requested performance metrics
2. Generate selected output formats
3. Compare to benchmark if specified
4. Return results to frontend

---

## API Response Structure

```json
{
  "status": "success",
  "backtest_id": "uuid",
  "results": {
    "summary": {
      "total_return": 45.2,
      "cagr": 12.3,
      "max_drawdown": -15.4,
      "sharpe_ratio": 1.82
    },
    "equity_curve": [
      {"date": "2020-01-01", "value": 10000},
      {"date": "2020-01-02", "value": 10050}
    ],
    "trades": [
      {
        "ticker": "AAPL",
        "entry_date": "2020-01-05",
        "entry_price": 150.00,
        "exit_date": "2020-02-10",
        "exit_price": 165.00,
        "shares": 10,
        "pnl": 150.00
      }
    ],
    "benchmark_comparison": {
      "alpha": 2.5,
      "beta": 0.95,
      "tracking_error": 3.2
    }
  }
}
```

---

## Dependencies & Tools

1. **Data Source**: AlphaVantage MCP for market data
2. **Numerical Processing**: Pandas, NumPy for data manipulation
3. **Backtesting Engine**: Custom engine or library like Backtrader/Zipline
4. **LLM Integration**: For parsing FinChat prompts into executable logic
5. **Performance Analytics**: QuantStats or custom calculations

---

## Next Steps for Implementation

Once this spec is approved, implementation will proceed in this order:

1. **Data Layer**: Market data fetching and preprocessing
2. **Strategy Engine**: Signal generation from prompts
3. **Execution Engine**: Order execution with costs/slippage
4. **Portfolio Manager**: Position tracking and risk management
5. **Analytics Engine**: Performance metrics and reporting
6. **API Layer**: Endpoints for job submission and result retrieval


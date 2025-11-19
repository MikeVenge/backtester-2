# Backtester Backend

A comprehensive backtesting engine for trading strategies with support for multiple asset classes, advanced risk management, and detailed performance analytics.

## Architecture

The backend is organized into several modules:

### Core Modules

1. **`backtest_engine.py`** - Main orchestration engine
   - Coordinates all components
   - Executes the backtest loop from time t to t+1
   - Handles data flow between modules

2. **`portfolio.py`** - Portfolio management
   - Tracks positions and cash
   - Manages risk limits
   - Calculates portfolio value and P&L
   - Records trades and equity curve

3. **`strategy.py`** - Strategy signal generation
   - Entry and exit signal logic
   - Position sizing calculations
   - Stop loss and take profit management
   - Signal ranking and filtering

4. **`data_fetcher.py`** - Market data acquisition
   - Fetches data from AlphaVantage MCP
   - Handles corporate actions (dividends, splits)
   - Aligns timestamps across tickers
   - Manages missing data

5. **`performance.py`** - Performance analytics
   - Calculates metrics (Sharpe, Sortino, Calmar, etc.)
   - Trade statistics
   - Benchmark comparisons
   - Export functionality

6. **`utils.py`** - Utility functions
   - Transaction cost calculations
   - Date/time helpers
   - Validation functions

7. **`models.py`** - Data models
   - Pydantic models for API requests
   - Configuration validation

8. **`main.py`** - FastAPI application
   - REST API endpoints
   - Job management
   - Background task execution

## Backtest Execution Flow (Time t → t+1)

### Phase 1: Pre-Processing at Time t
1. Load market data for timestamp t
2. Handle missing data (skip/forward-fill/interpolate)
3. Check if t is a valid trading day

### Phase 2: Execute Pending Orders
4. Execute entry/exit orders from previous bar (if `entryTiming=next-bar-open`)

### Phase 3: Mark-to-Market
5. Determine if MTM should occur based on frequency
6. Update prices for all positions
7. Calculate portfolio value
8. Record to equity curve

### Phase 4: Corporate Actions & Costs
9. Process dividend payments (if applicable)
10. Apply borrow costs for short positions

### Phase 5: Risk Monitoring
11. Calculate current drawdown (daily and weekly)
12. Check against max drawdown limits
13. Halt trading if limits exceeded

### Phase 6: Rebalancing
14. Check rebalancing conditions
15. Execute rebalancing trades (if triggered)

### Phase 7: Exit Processing
16. For each open position:
    - Check stop loss (fixed/trailing/volatility-based)
    - Check take profit
    - Check time-based exit
    - Check strategy exit signal
17. Execute exit orders
18. Update cash and close positions

### Phase 8: Entry Processing
19. Check if new entries allowed (not halted, under max positions)
20. Filter eligible universe
21. Generate entry signals
22. Rank signals if more than available slots
23. Calculate position sizes
24. Validate risk limits
25. Execute entry orders
26. Deduct costs from cash

### Phase 9: End-of-Period
27. Update position tracking
28. Log state
29. Increment to t+1

## API Endpoints

### POST /run_backtest
Submit a backtest job for execution.

**Request Body:**
```json
{
  "name": "My Strategy",
  "data": {
    "marketData": { ... },
    "strategy": { ... },
    "portfolioRisk": { ... },
    ...
  }
}
```

**Response:**
```json
{
  "status": "queued",
  "job_id": "uuid",
  "message": "Backtest queued for execution"
}
```

### GET /backtest_status/{job_id}
Get the status of a backtest job.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "running|completed|failed"
}
```

### GET /backtest_results/{job_id}
Get full results of a completed backtest.

**Response:**
```json
{
  "status": "success",
  "summary": {
    "total_return": 45.2,
    "cagr": 12.3,
    "sharpe_ratio": 1.82,
    ...
  },
  "equity_curve": [...],
  "trades": [...],
  ...
}
```

### GET /list_backtests
List all backtest jobs.

### DELETE /backtest_results/{job_id}
Delete a backtest job and its results.

## Installation

```bash
cd backend
pip install -r requirements.txt

# set AlphaVantage API key (required)
export ALPHAVANTAGE_API_KEY="your_api_key"
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Configuration

The backtest accepts configuration for 8 main sections:

1. **Market Data** - Tickers, date range, frequency, corporate actions
2. **Strategy Definition** - Entry/exit logic, position sizing, max positions
3. **Portfolio & Risk** - Initial capital, leverage, risk limits, drawdowns
4. **Trading Execution** - Order timing, commissions, slippage, short selling
5. **Mark-to-Market** - MTM frequency, pricing method, FX handling
6. **Rebalancing** - Rebalancing rules, universe management
7. **Output & Evaluation** - Performance metrics, output formats
8. **Implementation Details** - Data format preferences

## Data Source

The system uses **AlphaVantage MCP** for all market data:
- OHLCV data (intraday, daily, weekly, monthly)
- Dividend history (DIVIDENDS endpoint)
- Split history (SPLITS endpoint)
- Delisting information (LISTING_STATUS endpoint)

> **Note:** You must provide an AlphaVantage API key via the `ALPHAVANTAGE_API_KEY` environment variable for the backend to fetch data.

## Extending the System

### Adding Custom Signal Functions

```python
def my_entry_signal(market_data, ticker, timestamp):
    # Your logic here
    return True  # or False

strategy_engine.set_entry_signal_function(my_entry_signal)
```

### Adding Custom Position Sizing

Modify the `calculate_position_size` method in `strategy.py` to add new sizing methods.

### Adding New Performance Metrics

Add calculation methods to the `PerformanceAnalyzer` class in `performance.py`.

## Logging

The system uses Python's built-in logging module. Logs include:
- Backtest execution progress
- Data fetching status
- Trade executions
- Errors and warnings

Configure logging level in `main.py`.

## Testing

Requires AlphaVantage MCP client for real market data. No mock data is provided.

## Production Considerations

1. **Database**: Replace in-memory dictionaries with proper database (PostgreSQL, MongoDB)
2. **Queue System**: Use Celery or similar for job queue management
3. **Caching**: Add Redis for caching market data
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Authentication**: Add user authentication and authorization
6. **Monitoring**: Add application monitoring (Sentry, DataDog)
7. **Scalability**: Deploy with load balancer for multiple workers

## License

Copyright © 2025. All rights reserved.


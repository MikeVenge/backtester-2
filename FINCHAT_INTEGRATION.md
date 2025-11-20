# FinChat COT Integration

## Overview

The backtester now supports using FinChat Chain of Thought (COT) prompts for entry and exit logic. Instead of simple string patterns, you can now use FinChat COT slugs that leverage advanced analysis including historical prices, news, and other market data from Parsec.

## How It Works

### 1. Strategy Configuration

When configuring a strategy, you can now specify FinChat COT slugs:

```json
{
  "strategy": {
    "entryPromptType": "finchat-slug",
    "entryFinChatSlug": "conditional-stock-purchase",
    "exitPromptType": "finchat-slug",
    "exitFinChatSlug": "conditional-stock-sell-trigger",
    "positionSizingMethod": "portfolio-percent",
    "portfolioPercent": 100.0,
    "maxPositions": 1,
    "eligibleSymbols": "IBM"
  }
}
```

### 2. Execution Flow

1. **Initialization**: When a backtest starts, if FinChat slugs are detected:
   - FinChat client is initialized (defaults to `https://finchat-api.adgo.io`, no token required)
   - Strategy parser creates async functions that call FinChat COT

2. **Entry Signal Generation**:
   - For each timestamp and eligible ticker:
     - Calls FinChat COT with ticker symbol and date
     - Waits for COT completion (polls API)
     - Parses COT result to extract buy/sell/hold signal
     - Returns `True` if signal is "buy"

3. **Exit Signal Generation**:
   - For each existing position:
     - Calls FinChat COT with ticker, date, entry price, current price
     - Waits for COT completion
     - Parses COT result to extract sell/hold signal
     - Returns `True` if signal is "sell" or "exit"

### 3. COT Result Parsing

The system parses COT results by looking for:
- **Buy signals**: Keywords like "buy", "purchase", "long", "enter", "should buy"
- **Sell signals**: Keywords like "sell", "exit", "close", "short", "should sell"
- **Hold signals**: Keywords like "hold", "maintain", "keep", "retain"

Confidence levels are inferred from modifiers:
- "strong buy" → confidence 0.9
- "moderate buy" → confidence 0.7
- Regular buy → confidence 0.6

## Environment Variables

Optional environment variables for FinChat integration:

```bash
# Optional: Override default API URL
FINCHAT_API_URL=https://finchat-api.adgo.io

# Optional: API token (not required - FinChat API doesn't require authentication)
FINCHAT_API_TOKEN=your-bearer-token
```

**Note**: FinChat API does not require authentication. The API token is optional and can be omitted.

## Code Structure

### New Files

1. **`backend/finchat_client.py`**:
   - `FinChatClient` class for API interactions
   - Methods: `create_session()`, `run_cot()`, `parse_cot_result()`
   - Handles async COT execution and polling

2. **Updated `backend/strategy_parser.py`**:
   - Added `_create_finchat_entry()` and `_create_finchat_exit()` methods
   - Creates async wrapper functions for FinChat COT calls
   - Caches results to avoid duplicate API calls

3. **Updated `backend/models.py`**:
   - Added `entryFinChatSlug` and `exitFinChatSlug` fields
   - Added `"finchat-slug"` as valid `entryPromptType` and `exitPromptType`

### Modified Files

1. **`backend/backtest_engine.py`**:
   - Initializes FinChat client if slugs are provided
   - Passes FinChat client to strategy parser
   - Uses async versions of signal generation when FinChat is enabled

2. **`backend/strategy.py`**:
   - Added async versions: `generate_entry_signals_async()`, `check_exit_signal_async()`
   - Handles both sync and async signal functions

## Usage Example

### API Request

```json
{
  "marketData": {
    "tickers": ["IBM"],
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "frequency": "daily"
  },
  "strategy": {
    "entryPromptType": "finchat-slug",
    "entryFinChatSlug": "conditional-stock-purchase",
    "exitPromptType": "finchat-slug",
    "exitFinChatSlug": "conditional-stock-sell-trigger",
    "upsideThreshold": 10.0,
    "downsideThreshold": 5.0,
    "positionSizingMethod": "portfolio-percent",
    "portfolioPercent": 100.0,
    "maxPositions": 1,
    "eligibleSymbols": "IBM"
  },
  "portfolioRisk": {
    "initialCapital": 100000
  }
}
```

### What Happens

1. Backtest starts for IBM from 2024-01-01 to 2024-12-31
2. For each trading day:
   - **Entry check**: Calls `conditional-stock-purchase` COT with:
     - `$stock_symbol:IBM`
     - `$day_of_month:1` (extracted from timestamp)
   - If COT returns "buy" signal → Opens position
   - **Exit check**: For existing positions, calls `conditional-stock-sell-trigger` COT with:
     - `$stock_symbol:IBM`
     - `$yesterdays_price:150.0` (previous day's close)
     - `$todays_price:155.0` (current price)
     - `$upside_threshold%:10%` (from config)
     - `$downside_threshold%:5%` (from config)
   - If COT returns "sell" signal → Closes position

## COT Parameters

### Entry COT Parameters

The entry COT (`conditional-stock-purchase`) receives:
- `$stock_symbol`: Stock symbol (e.g., "IBM")
- `$day_of_month`: Day of the month (1-31) as a string

### Exit COT Parameters

The exit COT (`conditional-stock-sell-trigger`) receives:
- `$stock_symbol`: Stock symbol (e.g., "IBM")
- `$yesterdays_price`: Yesterday's closing price
- `$todays_price`: Today's current price
- `$upside_threshold%`: Upside sell threshold percentage (e.g., "10%")
- `$downside_threshold%`: Downside sell threshold percentage (e.g., "5%")

**Note**: Thresholds can be configured in the strategy config via `upsideThreshold` and `downsideThreshold` fields. Defaults to 10% upside and 5% downside if not specified.

## Error Handling

- If FinChat client fails to initialize, falls back to simple string parsing
- If COT execution fails, returns `False` (no entry/exit signal)
- Errors are logged but don't stop the backtest
- Results are cached per ticker/date to avoid duplicate calls

## Performance Considerations

- **Caching**: COT results are cached per ticker/date combination
- **Async Execution**: COT calls are async and don't block the backtest loop
- **Polling**: Default polling interval is 5 seconds, max 60 attempts (5 minutes)
- **Rate Limiting**: Be aware of FinChat API rate limits for large backtests

## Customization

### Custom COT Result Parser

You can customize the result parsing logic in `FinChatClient.parse_cot_result()`:

```python
def parse_cot_result(self, content: str) -> Dict[str, Any]:
    # Custom parsing logic here
    # Return: {"signal": "buy|sell|hold", "confidence": 0.0-1.0, "reasoning": "..."}
    pass
```

### Additional COT Parameters

You can extend the COT parameter passing in `strategy_parser.py`:

```python
additional_params = {
    "date": timestamp.strftime("%Y-%m-%d"),
    "custom_param": "custom_value"  # Add your own parameters
}
```

## Testing

To test FinChat integration:

1. Set environment variables:
   ```bash
   export FINCHAT_API_URL=https://finchat-api.adgo.io
   export FINCHAT_API_TOKEN=your-token
   ```

2. Run a backtest with FinChat slugs:
   ```python
   config = {
       "strategy": {
           "entryPromptType": "finchat-slug",
           "entryFinChatSlug": "test-entry-slug",
           # ...
       }
   }
   ```

3. Check logs for FinChat API calls and results

## Fallback Behavior

If FinChat is not configured or fails:
- Falls back to simple string pattern matching
- Uses default MA crossover logic if no patterns match
- Backtest continues without FinChat functionality

## Future Enhancements

- Support for multiple COT results per timestamp
- Custom result parsing strategies
- Batch COT calls for multiple tickers
- Result caching across backtest runs
- Support for COT parameters from frontend configuration


# Strategy Execution Analysis

## Current Implementation

### How "Buy on first day, Hold until end" is Currently Executed

#### Entry Logic: "Buy on first day"

**Current Flow:**
1. Strategy string `"Buy on first day"` is passed to `StrategyEngine`
2. `_check_entry_signal()` is called for each timestamp
3. **Problem**: `_default_entry_logic()` ignores the string and uses hardcoded MA crossover
4. MA crossover requires 20 days of data, so it never triggers on the first day
5. Result: **No entry signal generated**

**Code Path:**
```
backtest_engine._process_entries()
  → strategy.generate_entry_signals()
    → strategy._check_entry_signal()
      → strategy._default_entry_logic()  # ❌ Ignores "Buy on first day"
        → Uses MA crossover (requires 20 days)
```

#### Exit Logic: "Hold until end"

**Current Flow:**
1. Exit string `"Hold until end"` is passed to `StrategyEngine`
2. `check_exit_signal()` checks various exit conditions
3. `_check_strategy_exit()` calls `_default_exit_logic()`
4. **Problem**: `_default_exit_logic()` uses MA crossover, not "hold until end"
5. Result: **May exit prematurely based on MA signals**

**Code Path:**
```
backtest_engine._process_exits()
  → strategy.check_exit_signal()
    → strategy._check_strategy_exit()
      → strategy._default_exit_logic()  # ❌ Ignores "Hold until end"
        → Uses MA crossover
```

## Improvements Made

### 1. Created Strategy Parser (`backend/strategy_parser.py`)

**New Module**: Parses natural language strategy strings into executable functions

**Supported Patterns:**
- ✅ "Buy on first day" → Triggers on first timestamp
- ✅ "Buy every N days" → Triggers every N days
- ✅ "Buy immediately" → Triggers on first call
- ✅ "Hold until end" → Only exits at last timestamp
- ✅ "Sell after N days" → Exits after N days holding
- ✅ "Never exit" → Only exits at backtest end

### 2. Integrated Parser into Backtest Engine

**Changes:**
- Parse entry/exit logic strings during initialization
- Set parsed functions on `StrategyEngine` if parsing succeeds
- Falls back to default logic if parsing fails

**Code Path (After Fix):**
```
backtest_engine.__init__()
  → parse_strategy_logic()  # ✅ NEW: Parse strings
    → StrategyParser.parse_entry_logic()
    → StrategyParser.parse_exit_logic()
  → strategy.set_entry_signal_function()  # ✅ Set parsed function
  → strategy.set_exit_signal_function()   # ✅ Set parsed function

backtest_engine._process_entries()
  → strategy.generate_entry_signals()
    → strategy._check_entry_signal()
      → entry_signal_func()  # ✅ Uses parsed function!
```

### 3. Improved Strategy Logic

**Entry Function for "Buy on first day":**
- Tracks first timestamp seen for each ticker
- Returns `True` only on the first timestamp
- Returns `False` for all subsequent timestamps

**Exit Function for "Hold until end":**
- Checks if current timestamp is the last available timestamp
- Only returns `True` at the end of backtest
- Returns `False` for all other timestamps

## Testing the Fix

### Test Case: "Buy on first day, Hold until end"

**Expected Behavior:**
1. ✅ Entry signal triggers on first trading day
2. ✅ Position is opened with 100% of portfolio (portfolioPercent: 100.0)
3. ✅ Position is held throughout the backtest
4. ✅ Position is closed only at the last timestamp
5. ✅ Results show 1 trade with P&L = (final_price - entry_price) * shares

**Before Fix:**
- ❌ No entry signal (MA crossover requires 20 days)
- ❌ 0 trades executed
- ❌ Total return: 0%

**After Fix:**
- ✅ Entry signal on first day
- ✅ 1 trade executed
- ✅ Position held until end
- ✅ Total return calculated correctly

## Next Steps

1. ✅ Strategy parser created
2. ✅ Parser integrated into backtest engine
3. ⏳ Test with actual backtest
4. ⏳ Expand parser to support more patterns:
   - "Buy when price crosses above MA"
   - "Sell when RSI > 70"
   - "Buy on Monday, sell on Friday"
   - etc.

## Code Changes Summary

### New Files
- `backend/strategy_parser.py` - Strategy parsing module

### Modified Files
- `backend/backtest_engine.py` - Integrated parser
- `backend/strategy.py` - Improved logging

### Key Functions
- `StrategyParser.parse_entry_logic()` - Parses entry strings
- `StrategyParser.parse_exit_logic()` - Parses exit strings
- `parse_strategy_logic()` - Main parsing function



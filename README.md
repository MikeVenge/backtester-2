# Backtester - Trading Strategy Backtesting System

A comprehensive backtesting system with a React frontend and FastAPI backend, designed for testing trading strategies with real market data.

## Project Structure

```
backtester-2/
├── frontend/          # React frontend (deploy to Vercel)
│   ├── src/           # React components
│   ├── package.json    # Frontend dependencies
│   └── vercel.json     # Vercel deployment config
├── backend/            # FastAPI backend (deploy to Railway)
│   ├── main.py         # FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── ...
├── Procfile            # Railway deployment config
├── railway.json        # Railway configuration
└── requirements.txt    # Backend dependencies (for Railway)
```

## Quick Start

### Frontend (Local Development)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Backend (Local Development)

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run the backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### Configure Frontend to Connect to Backend

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Deployment

### Backend (Railway)

See `backend/RAILWAY_DEPLOYMENT.md` for detailed instructions.

Quick steps:
1. Connect GitHub repo to Railway
2. Set `ALPHAVANTAGE_API_KEY` environment variable
3. Deploy (Railway auto-detects Python)

### Frontend (Vercel)

See `frontend/README.md` for detailed instructions.

Quick steps:
1. Connect GitHub repo to Vercel
2. Set root directory to `frontend`
3. Set `VITE_API_URL` environment variable to your Railway backend URL
4. Deploy

## Documentation

- **Frontend**: See `frontend/README.md`
- **Backend API**: See `backend/API.md`
- **Backend Deployment**: See `backend/RAILWAY_DEPLOYMENT.md`
- **Backend Implementation**: See `BACKEND_IMPLEMENTATION_SUMMARY.md`
- **Backend Specification**: See `BACKEND_SPECIFICATION.md`

The UI provides a tabbed interface where you can configure all backtester parameters across 8 sections:
1. Market Data
2. Strategy Definition
3. Portfolio & Risk Settings
4. Trading & Execution Assumptions
5. Mark-to-Market (MTM) Settings
6. Rebalancing Rules
7. Output & Evaluation Preferences
8. Implementation Details

## Table of Contents

1. [Market Data](#1-market-data)
2. [Strategy Definition](#2-strategy-definition)
3. [Portfolio & Risk Settings](#3-portfolio--risk-settings)
4. [Trading & Execution Assumptions](#4-trading--execution-assumptions)
5. [Mark-to-Market (MTM) Settings](#5-mark-to-market-mtm-settings)
6. [Rebalancing Rules](#6-rebalancing-rules)
7. [Output & Evaluation Preferences](#7-output--evaluation-preferences)
8. [Practical Implementation Details](#8-practical-implementation-details)

---

## 1. Market Data

### Price Data

- **Ticker(s) / symbol(s)**: Stock symbols to backtest
- **Data fields**: Usually Open, High, Low, Close, Volume (OHLCV)
- **Data frequency**: 
  - Tick
  - 1-minute
  - 5-minute
  - Hourly
  - Daily
  - Weekly
- **Date range**: Range to test over (e.g., 2015-01-01 to 2025-01-01)

### Corporate Actions (Optional but Ideal)

- **Dividends**: Dividend payment data
- **Splits**: Stock split events
- **Delistings / mergers**: Corporate action events that affect trading

### Benchmark Data (Optional)

- **Index or asset**: Asset to compare against (e.g., SPY, BTC)

---

## 2. Strategy Definition

### Entry Rules

- Exact logic for when to open a position
- Examples:
  - Buy when 50-day MA crosses above 200-day MA
  - Long when RSI < 30, exit when RSI > 50

### Exit Rules

- When to close / reduce a position
- Types:
  - Take-profit levels
  - Stop-loss levels
  - Indicator crossovers
  - Time-based exits (e.g., hold for 5 days)

### Position Sizing Rules

- How much to buy/sell on each signal:
  - Fixed dollar amount
  - Percentage of portfolio
  - Risk-based (e.g., 1% of equity per trade based on ATR stop)
- **Max number of concurrent positions**: Limit on simultaneous holdings

### Universe / Selection Rules (for multi-asset strategies)

- Which symbols can be traded
- Ranking or filtering logic (e.g., top 10 by momentum)

---

## 3. Portfolio & Risk Settings

### Initial Capital

- Starting cash (e.g., $10,000 or 1 BTC)

### Leverage

- Allowed or not?
- If yes, max leverage (e.g., 2x, 5x, etc.)

### Position & Exposure Limits

- Max % in a single asset
- Max % in a sector (if relevant)
- Max net long/short exposure

### Risk Management Rules

- **Stop-loss**: Fixed %, volatility-based, dollar-based
- **Take-profit rules**: Profit target levels
- **Trailing stops**: Dynamic stop-loss adjustment
- **Max daily/weekly drawdown**: Threshold before halting trading

---

## 4. Trading & Execution Assumptions

### Order Type & Execution Timing

- **Entry timing**: 
  - Next bar open
  - Same bar close
  - Midpoint
  - VWAP
- **Order types**: Market orders vs limit orders (and limit logic if needed)

### Transaction Cost Model

- **Commissions**: Per trade or per share / contract
- **Fees**: Exchange fees
- **Bid-ask spread or slippage**: Assumption (e.g., 0.02% per trade)

### Trading Calendar & Availability

- Which days & hours trading can occur
- Handling of holidays, weekends, missing data

### Short Selling Rules

- Allowed or not?
- Borrow cost or constraints

---

## 5. Mark-to-Market (MTM) Settings

### MTM Frequency

Options:
- **Every bar** (e.g., every day for daily data, every minute for intraday) - most common
- Daily
- Weekly
- Monthly

In code, this is usually:
- "Recompute portfolio value at the end of each bar" (most common), or
- "Resample P&L to weekly/monthly for reporting only."

### Price Used for MTM

- **Close price**: Typical for EOD data
- **VWAP / mid / last**: For intraday / more detailed sims
- **Custom rule**: e.g., "mark long at bid, short at ask" to be conservative

### FX / Multi-Currency MTM (if relevant)

- **Base currency**: e.g., USD
- **FX rates source & frequency**: Daily, intraday
- Whether to MTM FX exposures separately

### Corporate Action Handling

- Whether to adjust historical prices for splits / dividends
- Whether to explicitly book dividend cashflows on ex-date/pay-date

In most backtesters, MTM is effectively "every bar", but you can still aggregate results at weekly/monthly level for analysis.

---

## 6. Rebalancing Rules

### Rebalancing Frequency / Trigger

#### Calendar-based:
- Daily / weekly / monthly / quarterly
- e.g., "Rebalance on the first trading day of each month."

#### Threshold-based:
- Only rebalance if weight drift > X% (e.g., if positions deviate > 5% from target weights)

#### Signal-based:
- Only rebalance when a new signal is generated (e.g., ranking changes, entry/exit conditions triggered)

#### Hybrid:
- e.g., "Check monthly; rebalance if drift > 3% OR if signal changes."

### Universe Updates (Adding/Deleting Assets)

#### Rules for adding new names:
- e.g., "Include stocks that meet liquidity and market-cap filters at each monthly rebalance."

#### Rules for removing names:
- Drop delisted / suspended assets
- Drop names that fall below liquidity or price thresholds
- Exit positions in names that leave the eligible universe

### Rebalancing Method

- **Full rebalance to target weights**: 
  - e.g., each month: compute target weights and trade from current to target.
- **Partial rebalance / top-up**: 
  - Only trade to reduce largest deviations, or only add to underweights.
- **Buy-only** (for some strategies like DCA):
  - Never sell, only buy new units as cash comes in.
- **Turnover-limited**: 
  - Max total turnover per rebalance (e.g., 20% of portfolio per month).

### Min Trade Size Rules

- Ignore trades below X shares or Y notional to avoid tiny orders.

### Order and Cost Assumptions for Rebalancing

Same as for normal trades:
- Order type (market/limit)
- Slippage model
- Commission model
- Optional: separate settings for "rebalance trades" vs "alpha trades" if desired

---

## 7. Output & Evaluation Preferences

### Performance Metrics

#### Basic:
- Total return
- CAGR (Compound Annual Growth Rate)
- Max drawdown
- Volatility

#### Ratios:
- Sharpe ratio
- Sortino ratio
- Calmar ratio

#### Trade Stats:
- Win rate
- Average win/loss
- Profit factor
- Average holding period

### Reporting Style

- **Equity curve**: Portfolio value over time
- **Monthly/annual returns table**: Periodic performance breakdown
- **Distribution of drawdowns**: Drawdown analysis
- **Trade log**: Per trade details

### Benchmark Comparison

- What benchmark to compare against
- Whether to calculate alpha, beta, tracking error

---

## 8. Practical Implementation Details

### Programming Environment

- What you want to use: Python, Excel, another language?

### Data Format

- CSV, JSON, database, API source, etc.
- Column names & date format

---

## Summary: Complete Input Checklist

When setting up a backtest, ensure you have defined:

- ✅ **Market data** (symbols, OHLCV, date range, benchmark)
- ✅ **Strategy rules** (entry, exit, position sizing, universe selection)
- ✅ **Portfolio & risk settings** (initial capital, leverage, limits, stops)
- ✅ **Trading & execution assumptions** (order types, slippage, fees, shorting rules)
- ✅ **Mark-to-Market settings** (MTM frequency, price used, FX & corporate actions)
- ✅ **Rebalancing & universe management** (frequency, adding/removing assets, method)
- ✅ **Evaluation / reporting preferences** (metrics, output format)


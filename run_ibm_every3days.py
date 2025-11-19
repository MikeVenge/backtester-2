#!/usr/bin/env python3
"""
Run IBM backtest: buy 100 shares every 3 trading days, sell after 6 trading days.
Period: 2024-05-01 to 2025-05-01
"""
import asyncio
from datetime import datetime
from typing import Dict

from backend.backtest_engine import BacktestEngine


class EveryNthTradingDayStrategy:
    """Helper to trigger entries every N trading days and exit after holding M trading days."""

    def __init__(self, n_buy_days: int, hold_days: int):
        self.n_buy_days = n_buy_days
        self.hold_days = hold_days
        self.last_buy_index: Dict[str, int] = {}

    def should_buy(self, market_data, ticker: str, timestamp: datetime) -> bool:
        """Return True if we should enter on this trading day."""
        try:
            ticker_data = market_data.xs(ticker, level="ticker")
            idx = ticker_data.index.get_loc(timestamp)
        except Exception:
            return False

        last_idx = self.last_buy_index.get(ticker)
        if last_idx is None or idx - last_idx >= self.n_buy_days:
            self.last_buy_index[ticker] = idx
            return True
        return False

    def should_exit(self, market_data, ticker: str, timestamp: datetime, position) -> bool:
        """Exit once we've held for the configured number of trading days."""
        try:
            ticker_data = market_data.xs(ticker, level="ticker")
            current_idx = ticker_data.index.get_loc(timestamp)
            entry_idx = ticker_data.index.get_loc(position.entry_timestamp)
        except Exception:
            return False

        return (current_idx - entry_idx) >= self.hold_days


async def run_backtest():
    config = {
        "marketData": {
            "tickers": "IBM",
            "fields": ["open", "high", "low", "close", "volume"],
            "frequency": "daily",
            "startDate": "2024-05-01",
            "endDate": "2025-05-01",
            "includeDividends": False,
            "includeSplits": False,
            "includeDelistings": False,
        },
        "strategy": {
            "entryLogic": "custom",
            "exitLogic": "custom",
            "timeBasedExit": None,
            "maxPositions": 10,
        },
        "portfolioRisk": {
            "initialCapital": 1_000_000.0,
            "leverageAllowed": False,
            "maxLeverage": 1.0,
            "maxSingleAssetPercent": 100.0,
        },
        "tradingExecution": {
            "entryTiming": "same-bar-close",
            "orderType": "market",
            "commissionType": "per-trade",
            "commissionAmount": 1.0,
            "slippage": 0.0,
            "handleMissingData": "forward-fill",
            "shortSellingAllowed": False,
        },
        "mtm": {"mtmFrequency": "daily", "mtmPrice": "close"},
    }

    print("Initializing backtest engine...")
    engine = BacktestEngine(config)

    helper = EveryNthTradingDayStrategy(n_buy_days=3, hold_days=6)
    engine.strategy.set_entry_signal_function(helper.should_buy)
    engine.strategy.set_exit_signal_function(helper.should_exit)

    def fixed_hundred_shares(ticker, current_price, portfolio_value, cash_available):
        return 100

    engine.strategy.calculate_position_size = fixed_hundred_shares

    print("Running backtest...")
    results = await engine.run()

    summary = results.get("summary", {})
    trades = results.get("trades", [])
    print("\n=== TRADE LOG (all trades) ===")
    for idx, trade in enumerate(trades, 1):
        print(f"Trade {idx}:")
        print(f"  Entry: {trade.get('Entry Date')} @ ${trade.get('Entry Price')}")
        print(f"  Exit:  {trade.get('Exit Date')} @ ${trade.get('Exit Price')}")
        print(f"  Shares: {trade.get('Shares')}")
        print(f"  P&L: ${trade.get('P&L')} ({trade.get('P&L %')}%)")
        print(f"  Reason: {trade.get('Exit Reason')}")
        print("-" * 40)

    print("\n=== SUMMARY ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nTotal trades:", len(trades))
    return results


if __name__ == "__main__":
    asyncio.run(run_backtest())


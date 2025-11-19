#!/usr/bin/env python3
"""
Simple CLI script to test backtesting with IBM stock
Strategy: Buy 100 shares every 3 days, hold for 3 days, then sell
"""
import asyncio
import json
from datetime import datetime
from backend.backtest_engine import BacktestEngine
from backend.simple_strategies import create_rotation_strategy_functions


async def run_ibm_backtest():
    """Run a simple backtest on IBM stock"""
    
    print("=" * 60)
    print("IBM Backtest: Buy & Hold for 3 Days Strategy")
    print("=" * 60)
    print()
    
    # Configuration for the backtest
    config = {
        'marketData': {
            'tickers': 'IBM',
            'fields': ['open', 'high', 'low', 'close', 'volume'],
            'frequency': 'daily',
            'startDate': '2024-01-01',
            'endDate': '2025-01-01',
            'includeDividends': True,
            'includeSplits': True,
            'includeDelistings': False,
            'benchmark': None
        },
        'strategy': {
            'entryLogic': 'Buy every 3 days',
            'entryPromptType': 'string',
            'entryFinChatPrompt': 'Buy every 3 days',
            'exitLogic': 'Sell after 3 days',
            'exitPromptType': 'string',
            'exitFinChatPrompt': 'Sell after 3 days',
            'takeProfit': None,  # No take profit
            'stopLoss': None,     # No stop loss
            'timeBasedExit': 3,   # Exit after 3 days
            'positionSizingMethod': 'fixed-dollar',
            'fixedDollarAmount': None,  # Will be calculated based on 100 shares
            'portfolioPercent': None,
            'riskPercent': None,
            'maxPositions': 100,  # Allow multiple overlapping positions
            'eligibleSymbols': 'IBM',
            'rankingLogic': None
        },
        'portfolioRisk': {
            'initialCapital': 1000000.0,  # $1M starting capital
            'leverageAllowed': False,
            'maxLeverage': 1.0,
            'maxSingleAssetPercent': 100.0,  # Allow full allocation
            'maxSectorPercent': 100.0,
            'maxNetExposure': 100.0,
            'stopLossType': 'fixed-percent',
            'useTrailingStops': False,
            'trailingStopDistance': None,
            'maxDailyDrawdown': None,  # No drawdown limits for this test
            'maxWeeklyDrawdown': None
        },
        'tradingExecution': {
            'entryTiming': 'same-bar-close',  # Execute at close of signal bar
            'orderType': 'market',
            'commissionType': 'per-trade',
            'commissionAmount': 1.0,  # $1 per trade
            'exchangeFees': 0.0,
            'slippage': 0.0,  # No slippage for testing
            'tradingDays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'handleMissingData': 'forward-fill',
            'shortSellingAllowed': False,
            'borrowCost': 0.0
        },
        'mtm': {
            'mtmFrequency': 'daily',
            'mtmPrice': 'close',
            'baseCurrency': 'USD',
            'fxFrequency': 'daily',
            'mtmFXSeparately': False,
            'adjustForSplitsDividends': True,
            'bookDividendCashflows': True
        },
        'rebalancing': {
            'rebalancingType': None,
            'dropDelisted': False,
            'dropBelowThresholds': False,
            'exitIneligible': False,
            'rebalancingMethod': 'full',
            'minShares': 1,
            'minNotional': 0.0
        },
        'output': {
            'basicMetrics': ['Total Return', 'CAGR', 'Max Drawdown', 'Volatility'],
            'ratioMetrics': ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio'],
            'tradeStats': ['Win Rate', 'Average Win/Loss', 'Profit Factor', 'Average Holding Period'],
            'outputFormats': ['Equity Curve', 'Trade Log'],
            'benchmarkSymbol': None,
            'benchmarkMetrics': []
        },
        'implementation': {
            'programmingEnv': 'python',
            'dataFormat': 'json',
            'columnNames': 'timestamp,open,high,low,close,volume',
            'dateFormat': 'YYYY-MM-DD'
        }
    }
    
    print("Configuration:")
    print(f"  Ticker: IBM")
    print(f"  Period: 2024-01-01 to 2025-01-01")
    print(f"  Strategy: Buy 100 shares every 3 days, hold for 3 days")
    print(f"  Initial Capital: $1,000,000")
    print(f"  Commission: $1 per trade")
    print()
    print("Starting backtest...")
    print()
    
    try:
        # Initialize backtest engine
        engine = BacktestEngine(config)
        
        # Set up custom rotation strategy (buy every 3 days, hold for 3 days)
        entry_func, exit_func = create_rotation_strategy_functions(
            buy_every_n_days=3,
            hold_for_days=3
        )
        engine.strategy.set_entry_signal_function(entry_func)
        engine.strategy.set_exit_signal_function(exit_func)
        
        # Override position sizing to buy exactly 100 shares
        original_calc = engine.strategy.calculate_position_size
        def fixed_100_shares(ticker, current_price, portfolio_value, cash_available):
            return 100  # Always buy 100 shares
        engine.strategy.calculate_position_size = fixed_100_shares
        
        # Run backtest
        results = await engine.run()
        
        print("=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print()
        
        # Display summary metrics
        summary = results.get('summary', {})
        
        print("Performance Metrics:")
        print("-" * 60)
        print(f"  Initial Capital:    ${summary.get('initial_capital', 0):,.2f}")
        print(f"  Final Value:        ${summary.get('final_value', 0):,.2f}")
        print(f"  Total Return:       {summary.get('total_return', 0):.2f}%")
        print(f"  CAGR:              {summary.get('cagr', 0):.2f}%")
        print(f"  Max Drawdown:      {summary.get('max_drawdown', 0):.2f}%")
        print(f"  Volatility:        {summary.get('volatility', 0):.2f}%")
        print()
        
        print("Risk-Adjusted Returns:")
        print("-" * 60)
        print(f"  Sharpe Ratio:      {summary.get('sharpe_ratio', 0):.2f}")
        print(f"  Sortino Ratio:     {summary.get('sortino_ratio', 0):.2f}")
        print(f"  Calmar Ratio:      {summary.get('calmar_ratio', 0):.2f}")
        print()
        
        print("Trade Statistics:")
        print("-" * 60)
        print(f"  Total Trades:      {summary.get('total_trades', 0)}")
        print(f"  Winning Trades:    {summary.get('winning_trades', 0)}")
        print(f"  Losing Trades:     {summary.get('losing_trades', 0)}")
        print(f"  Win Rate:          {summary.get('win_rate', 0):.2f}%")
        print(f"  Avg Win:           ${summary.get('average_win', 0):,.2f}")
        print(f"  Avg Loss:          ${summary.get('average_loss', 0):,.2f}")
        print(f"  Profit Factor:     {summary.get('profit_factor', 0):.2f}")
        print(f"  Avg Hold Period:   {summary.get('average_holding_period', 0):.1f} days")
        print()
        
        # Display first few trades
        trades = results.get('trades', [])
        if trades:
            print("Sample Trades (first 5):")
            print("-" * 60)
            for i, trade in enumerate(trades[:5], 1):
                print(f"  Trade {i}:")
                print(f"    Entry: {trade.get('Entry Date')} @ ${trade.get('Entry Price', 0):.2f}")
                print(f"    Exit:  {trade.get('Exit Date')} @ ${trade.get('Exit Price', 0):.2f}")
                print(f"    Shares: {trade.get('Shares', 0)}")
                print(f"    P&L: ${trade.get('P&L', 0):,.2f} ({trade.get('P&L %', 0):.2f}%)")
                print(f"    Reason: {trade.get('Exit Reason', 'N/A')}")
                print()
        
        if len(trades) > 5:
            print(f"  ... and {len(trades) - 5} more trades")
            print()
        
        # Display current positions
        positions = results.get('positions', [])
        if positions:
            print("Open Positions:")
            print("-" * 60)
            for pos in positions:
                print(f"  {pos.get('ticker')}: {pos.get('shares')} shares @ ${pos.get('entry_price', 0):.2f}")
                print(f"    Current: ${pos.get('current_price', 0):.2f}")
                print(f"    P&L: ${pos.get('pnl', 0):,.2f} ({pos.get('pnl_percent', 0):.2f}%)")
                print()
        
        # Save full results to file
        output_file = 'ibm_backtest_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Full results saved to: {output_file}")
        print()
        
        return results
        
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print()
    print("IBM Backtest CLI Tool")
    print("Testing strategy: Buy 100 shares every 3 days, hold for 3 days")
    print()
    
    # Run the backtest
    results = asyncio.run(run_ibm_backtest())
    
    if results:
        print("=" * 60)
        print("Backtest completed successfully!")
        print("=" * 60)
    else:
        print("Backtest failed. Check logs for details.")


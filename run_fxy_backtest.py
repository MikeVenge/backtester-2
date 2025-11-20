#!/usr/bin/env python3
"""
CLI script to run backtest for FXY using FinChat COT prompts
Period: Jan 1, 2025 to March 31, 2025
"""
import asyncio
import json
from datetime import datetime
from backend.backtest_engine import BacktestEngine


async def run_fxy_backtest():
    """Run backtest on FXY stock using FinChat COT"""
    
    print("=" * 60)
    print("FXY Backtest: FinChat COT Strategy")
    print("=" * 60)
    print()
    
    # Configuration for the backtest
    config = {
        'marketData': {
            'tickers': 'FXY',
            'fields': ['open', 'high', 'low', 'close', 'volume', 'adjusted_close'],
            'frequency': 'daily',
            'startDate': '2025-01-01',
            'endDate': '2025-03-31',
            'includeDividends': True,
            'includeSplits': True,
            'includeDelistings': False,
            'benchmark': None
        },
        'strategy': {
            'entryPromptType': 'finchat-slug',
            'entryFinChatSlug': 'conditional-stock-purchase',
            'exitPromptType': 'finchat-slug',
            'exitFinChatSlug': 'conditional-stock-sell-trigger',
            'upsideThreshold': 10.0,
            'downsideThreshold': 5.0,
            'positionSizingMethod': 'portfolio-percent',
            'portfolioPercent': 100.0,
            'maxPositions': 1,
            'eligibleSymbols': 'FXY',
            'takeProfit': None,
            'stopLoss': None,
            'timeBasedExit': None,
            'rankingLogic': None
        },
        'portfolioRisk': {
            'initialCapital': 100000.0,  # $100K starting capital
            'leverageAllowed': False,
            'maxLeverage': 1.0,
            'maxSingleAssetPercent': 100.0,
            'maxSectorPercent': 100.0,
            'maxNetExposure': 100.0,
            'stopLossType': 'fixed-percent',
            'useTrailingStops': False,
            'trailingStopDistance': None,
            'maxDailyDrawdown': None,
            'maxWeeklyDrawdown': None
        },
        'tradingExecution': {
            'entryTiming': 'next-bar-open',
            'orderType': 'market',
            'commissionType': 'per-trade',
            'commissionAmount': 1.0,
            'exchangeFees': 0.0,
            'slippage': 0.0,
            'tradingDays': [],
            'handleMissingData': 'skip',
            'shortSellingAllowed': False,
            'borrowCost': 0.0
        },
        'mtm': {
            'mtmFrequency': 'every-bar',
            'mtmPrice': 'close',
            'baseCurrency': 'USD',
            'fxFrequency': 'daily',
            'mtmFXSeparately': False,
            'adjustForSplitsDividends': True,
            'bookDividendCashflows': False
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
    print(f"  Ticker: FXY")
    print(f"  Period: 2025-01-01 to 2025-03-31")
    print(f"  Entry COT: conditional-stock-purchase")
    print(f"  Exit COT: conditional-stock-sell-trigger")
    print(f"  Upside Threshold: 10%")
    print(f"  Downside Threshold: 5%")
    print(f"  Position Sizing: 100% of portfolio")
    print(f"  Initial Capital: $100,000")
    print()
    print("Starting backtest...")
    print()
    
    try:
        # Initialize backtest engine
        engine = BacktestEngine(config)
        
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
        
        # Display all trades
        trades = results.get('trades', [])
        if trades:
            print(f"All Trades ({len(trades)} total):")
            print("-" * 60)
            for i, trade in enumerate(trades, 1):
                print(f"  Trade {i}:")
                print(f"    Entry: {trade.get('Entry Date')} @ ${trade.get('Entry Price', 0):.2f}")
                print(f"    Exit:  {trade.get('Exit Date')} @ ${trade.get('Exit Price', 0):.2f}")
                print(f"    Shares: {trade.get('Shares', 0)}")
                print(f"    P&L: ${trade.get('P&L', 0):,.2f} ({trade.get('P&L %', 0):.2f}%)")
                print(f"    Reason: {trade.get('Exit Reason', 'N/A')}")
                print()
        else:
            print("No trades executed.")
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
        output_file = 'fxy_backtest_results.json'
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
    print("FXY Backtest CLI Tool")
    print("Using FinChat COT for entry/exit signals")
    print()
    
    # Run the backtest
    results = asyncio.run(run_fxy_backtest())
    
    if results:
        print("=" * 60)
        print("Backtest completed successfully!")
        print("=" * 60)
    else:
        print("Backtest failed. Check logs for details.")


#!/usr/bin/env python3
"""
CLI script to run FXY backtest via Railway API endpoint
Period: Jan 1, 2025 to March 31, 2025
Uses FinChat COT for entry/exit signals
"""
import requests
import json
import time
import os
from datetime import datetime

# Railway backend URL
RAILWAY_URL = os.getenv("RAILWAY_URL", "https://backtester-2-production.up.railway.app")

def create_fxy_backtest_config():
    """Create FXY backtest configuration"""
    return {
        "name": f"FXY FinChat COT Backtest - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "data": {
            "marketData": {
                "tickers": "FXY",
                "fields": ["open", "high", "low", "close", "volume", "adjusted_close"],
                "frequency": "daily",
                "startDate": "2025-01-01",
                "endDate": "2025-01-15",
                "includeDividends": True,
                "includeSplits": True,
                "includeDelistings": False,
                "benchmark": None
            },
            "strategy": {
                "entryPromptType": "finchat-slug",
                "entryFinChatSlug": "conditional-stock-purchase",
                "exitPromptType": "finchat-slug",
                "exitFinChatSlug": "conditional-stock-sell-trigger",
                "upsideThreshold": 0.01,  # 0.01 = 1% as decimal
                "downsideThreshold": 0.01,  # 0.01 = 1% as decimal
                "positionSizingMethod": "fixed-dollar",
                "fixedDollarAmount": 10000.0,  # $10,000 notional per trade
                "maxPositions": 1,
                "eligibleSymbols": "FXY",
                "takeProfit": None,
                "stopLoss": None,
                "timeBasedExit": None,
                "rankingLogic": None
            },
            "portfolioRisk": {
                "initialCapital": 100000.0,
                "leverageAllowed": False,
                "maxLeverage": 1.0,
                "maxSingleAssetPercent": 100.0,
                "maxSectorPercent": 100.0,
                "maxNetExposure": 100.0,
                "stopLossType": "fixed-percent",
                "useTrailingStops": False,
                "trailingStopDistance": None,
                "maxDailyDrawdown": None,
                "maxWeeklyDrawdown": None
            },
            "tradingExecution": {
                "entryTiming": "same-bar-close",  # Execute at close of signal bar
                "orderType": "market",
                "commissionType": "per-trade",
                "commissionAmount": 1.0,
                "exchangeFees": 0.0,
                "slippage": 0.0,
                "tradingDays": [],
                "handleMissingData": "skip",
                "shortSellingAllowed": False,
                "borrowCost": 0.0
            },
            "mtm": {
                "mtmFrequency": "every-bar",
                "mtmPrice": "close",
                "baseCurrency": "USD",
                "fxFrequency": "daily",
                "mtmFXSeparately": False,
                "adjustForSplitsDividends": True,
                "bookDividendCashflows": False
            },
            "rebalancing": {
                "rebalancingType": None,
                "dropDelisted": False,
                "dropBelowThresholds": False,
                "exitIneligible": False,
                "rebalancingMethod": "full",
                "minShares": 1,
                "minNotional": 0.0
            },
            "output": {
                "basicMetrics": ["Total Return", "CAGR", "Max Drawdown", "Volatility"],
                "ratioMetrics": ["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio"],
                "tradeStats": ["Win Rate", "Average Win/Loss", "Profit Factor", "Average Holding Period"],
                "outputFormats": ["Equity Curve", "Trade Log"],
                "benchmarkSymbol": None,
                "benchmarkMetrics": []
            },
            "implementation": {
                "programmingEnv": "python",
                "dataFormat": "json",
                "columnNames": "timestamp,open,high,low,close,volume",
                "dateFormat": "YYYY-MM-DD"
            }
        }
    }

def submit_backtest():
    """Submit backtest to Railway API"""
    print("=" * 80)
    print("FXY Backtest via Railway API")
    print("=" * 80)
    print()
    print(f"Railway URL: {RAILWAY_URL}")
    print(f"Ticker: FXY")
    print(f"Period: 2025-01-01 to 2025-01-15")
    print(f"Entry COT: conditional-stock-purchase")
    print(f"Exit COT: conditional-stock-sell-trigger")
    print()
    
    # Check health first
    print("Checking Railway backend health...")
    try:
        health_response = requests.get(f"{RAILWAY_URL}/health", timeout=10)
        health_response.raise_for_status()
        print(f"✓ Railway backend is healthy")
    except Exception as e:
        print(f"✗ Railway backend health check failed: {e}")
        return None
    
    # Submit backtest
    print()
    print("Submitting backtest job...")
    config = create_fxy_backtest_config()
    
    try:
        response = requests.post(
            f"{RAILWAY_URL}/run_backtest",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        job_id = data.get('job_id')
        print(f"✓ Backtest job submitted")
        print(f"  Job ID: {job_id}")
        print(f"  Status: {data.get('status')}")
        print()
        
        return job_id
    except Exception as e:
        print(f"✗ Failed to submit backtest: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"  Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"  Response: {e.response.text}")
        return None

def poll_status(job_id, max_wait=600):
    """Poll for backtest completion"""
    if not job_id:
        return None
    
    print("=" * 80)
    print("Polling for Backtest Completion")
    print("=" * 80)
    print()
    print("Note: FinChat COT calls may take time. This could take several minutes...")
    print()
    
    start_time = time.time()
    check_interval = 5
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{RAILWAY_URL}/backtest_status/{job_id}", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            status = data.get('status')
            elapsed = int(time.time() - start_time)
            
            print(f"[{elapsed:4d}s] Status: {status}")
            
            if status == "completed":
                print(f"\n✓ Backtest completed in {elapsed} seconds")
                return True
            elif status == "failed":
                print(f"\n✗ Backtest failed")
                # Try to get error details
                try:
                    error_response = requests.get(f"{RAILWAY_URL}/backtest_results/{job_id}", timeout=10)
                    if error_response.status_code == 200:
                        error_data = error_response.json()
                        if 'error' in error_data:
                            print(f"  Error: {error_data['error']}")
                        if 'error_traceback' in error_data:
                            print(f"\n  Traceback:")
                            print(f"  {error_data['error_traceback'][:500]}")
                except:
                    pass
                if 'error' in data:
                    print(f"  Error: {data['error']}")
                return False
            
            time.sleep(check_interval)
        except Exception as e:
            print(f"✗ Error checking status: {e}")
            time.sleep(check_interval)
    
    print(f"\n✗ Backtest did not complete within {max_wait} seconds")
    return False

def get_results(job_id):
    """Get backtest results"""
    if not job_id:
        return None
    
    print()
    print("=" * 80)
    print("Retrieving Backtest Results")
    print("=" * 80)
    print()
    
    try:
        response = requests.get(f"{RAILWAY_URL}/backtest_results/{job_id}", timeout=30)
        response.raise_for_status()
        
        results = response.json()
        
        # Display summary
        summary = results.get('summary', {})
        
        print("Performance Metrics:")
        print("-" * 80)
        print(f"  Initial Capital:    ${summary.get('initial_capital', 0):,.2f}")
        print(f"  Final Value:        ${summary.get('final_value', 0):,.2f}")
        print(f"  Total Return:       {summary.get('total_return', 0):.2f}%")
        print(f"  CAGR:              {summary.get('cagr', 0):.2f}%")
        print(f"  Max Drawdown:      {summary.get('max_drawdown', 0):.2f}%")
        print(f"  Volatility:        {summary.get('volatility', 0):.2f}%")
        print()
        
        print("Trade Statistics:")
        print("-" * 80)
        print(f"  Total Trades:      {summary.get('total_trades', 0)}")
        print(f"  Winning Trades:    {summary.get('winning_trades', 0)}")
        print(f"  Losing Trades:     {summary.get('losing_trades', 0)}")
        print(f"  Win Rate:          {summary.get('win_rate', 0):.2f}%")
        print()
        
        # Display FinChat signals
        finchat_signals = results.get('finchat_signals', [])
        if finchat_signals:
            print(f"FinChat COT Signals ({len(finchat_signals)} total):")
            print("-" * 80)
            for i, signal in enumerate(finchat_signals, 1):
                signal_type = signal.get('type', 'unknown').upper()
                ticker = signal.get('ticker', 'N/A')
                timestamp = signal.get('timestamp', 'N/A')
                cot_signal = signal.get('signal', 'N/A').upper()
                confidence = signal.get('confidence', 0)
                cot_response = signal.get('cot_response', '')[:500]  # First 500 chars
                
                print(f"\n  Signal {i} - {signal_type} ({ticker})")
                print(f"    Date: {timestamp}")
                print(f"    Signal: {cot_signal}")
                print(f"    Confidence: {confidence:.2f}")
                if signal_type == 'ENTRY':
                    print(f"    Day of Month: {signal.get('day_of_month', 'N/A')}")
                elif signal_type == 'EXIT':
                    print(f"    Entry Price: ${signal.get('position_entry_price', 0):.2f}")
                    print(f"    Yesterday Price: ${signal.get('yesterday_price', 0):.2f}")
                    print(f"    Today Price: ${signal.get('today_price', 0):.2f}")
                print(f"    COT Response:")
                print(f"      {cot_response}")
                if len(signal.get('cot_response', '')) > 500:
                    print(f"      ... (truncated)")
                print()
        else:
            print("No FinChat signals recorded.")
            print()
        
        # Display all trades
        trades = results.get('trades', [])
        if trades:
            print(f"All Trades ({len(trades)} total):")
            print("-" * 80)
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
        
        # Save results
        output_file = f'fxy_railway_results_{job_id[:8]}.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Full results saved to: {output_file}")
        print()
        
        return results
    except Exception as e:
        print(f"✗ Failed to get results: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"  Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"  Response: {e.response.text}")
        return None

if __name__ == "__main__":
    print()
    print("FXY Backtest via Railway API")
    print("Using FinChat COT for entry/exit signals")
    print()
    
    # Submit backtest
    job_id = submit_backtest()
    
    if job_id:
        # Poll for completion
        completed = poll_status(job_id, max_wait=600)  # 10 minutes max
        
        if completed:
            # Get results
            results = get_results(job_id)
            
            if results:
                print("=" * 80)
                print("Backtest completed successfully!")
                print("=" * 80)
        else:
            print("\nBacktest did not complete. Check Railway logs for details.")
    else:
        print("\nFailed to submit backtest. Check Railway backend status.")


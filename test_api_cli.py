#!/usr/bin/env python3
"""
CLI script to test backend API endpoints using IBM as test symbol
Tests all API functions: health, run_backtest, status, results, list, delete
"""
import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
# Change this to your Railway backend URL for production testing
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_TICKER = "IBM"
TEST_START_DATE = "2024-05-01"
TEST_END_DATE = "2025-05-01"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

def test_health_check():
    """Test GET /health endpoint"""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print_success("Health check passed")
        print(f"  Status: {data.get('status')}")
        print(f"  Timestamp: {data.get('timestamp')}")
        print(f"  Active Backtests: {data.get('active_backtests', 0)}")
        return True
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {API_BASE_URL}")
        print_info("Make sure the backend is running: uvicorn backend.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False

def test_root_endpoint():
    """Test GET / endpoint"""
    print_header("TEST 2: Root Endpoint")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print_success("Root endpoint accessible")
        print(f"  Message: {data.get('message')}")
        print(f"  Version: {data.get('version')}")
        print(f"  Status: {data.get('status')}")
        return True
    except Exception as e:
        print_error(f"Root endpoint test failed: {str(e)}")
        return False

def create_ibm_backtest_config():
    """Create a test backtest configuration for IBM"""
    return {
        "name": f"IBM Test Backtest - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat() + "Z",
        "data": {
            "marketData": {
                "tickers": TEST_TICKER,
                "fields": ["open", "high", "low", "close", "volume"],
                "frequency": "daily",
                "startDate": TEST_START_DATE,
                "endDate": TEST_END_DATE,
                "includeDividends": True,
                "includeSplits": True,
                "includeDelistings": False,
                "benchmark": None
            },
            "strategy": {
                "entryLogic": "Buy every 3 business days",
                "entryPromptType": "string",
                "entryFinChatUrl": None,
                "entryFinChatPrompt": "Buy every 3 business days",
                "exitLogic": "Sell after 6 business days",
                "exitPromptType": "string",
                "exitFinChatUrl": None,
                "exitFinChatPrompt": "Sell after 6 business days",
                "takeProfit": None,
                "stopLoss": None,
                "timeBasedExit": 6,
                "positionSizingMethod": "fixed-dollar",
                "fixedDollarAmount": 10000.0,
                "portfolioPercent": None,
                "riskPercent": None,
                "maxPositions": 10,
                "eligibleSymbols": TEST_TICKER,
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
                "takeProfitRules": None,
                "useTrailingStops": False,
                "trailingStopDistance": None,
                "maxDailyDrawdown": None,
                "maxWeeklyDrawdown": None
            },
            "tradingExecution": {
                "entryTiming": "next-bar-open",
                "orderType": "market",
                "limitOrderLogic": None,
                "commissionType": "per-trade",
                "commissionAmount": 1.0,
                "exchangeFees": 0.0,
                "slippage": 0.0,
                "tradingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "handleMissingData": "forward-fill",
                "shortSellingAllowed": False,
                "borrowCost": 0.0,
                "shortConstraints": None
            },
            "mtm": {
                "mtmFrequency": "daily",
                "mtmPrice": "close",
                "baseCurrency": "USD",
                "fxFrequency": "daily",
                "mtmFXSeparately": False,
                "adjustForSplitsDividends": True,
                "bookDividendCashflows": True
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

def test_submit_backtest():
    """Test POST /run_backtest endpoint"""
    print_header("TEST 3: Submit Backtest Job")
    
    config = create_ibm_backtest_config()
    
    try:
        print_info(f"Submitting backtest for {TEST_TICKER} ({TEST_START_DATE} to {TEST_END_DATE})")
        print_info("Strategy: Buy every 3 days, sell after 6 days")
        
        response = requests.post(
            f"{API_BASE_URL}/run_backtest",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        print_success("Backtest job submitted successfully")
        print(f"  Job ID: {data.get('job_id')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Message: {data.get('message')}")
        
        config_summary = data.get('config_summary', {})
        print(f"  Ticker: {config_summary.get('tickers')}")
        print(f"  Start Date: {config_summary.get('start_date')}")
        print(f"  End Date: {config_summary.get('end_date')}")
        print(f"  Initial Capital: ${config_summary.get('initial_capital', 0):,.2f}")
        
        return data.get('job_id')
    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP error: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                print(f"  Error detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print_error(f"Submit backtest failed: {str(e)}")
        return None

def test_check_status(job_id):
    """Test GET /backtest_status/{job_id} endpoint"""
    print_header("TEST 4: Check Backtest Status")
    
    if not job_id:
        print_error("No job ID provided, skipping status check")
        return None
    
    try:
        print_info(f"Checking status for job: {job_id}")
        response = requests.get(f"{API_BASE_URL}/backtest_status/{job_id}", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print_success("Status retrieved successfully")
        print(f"  Job ID: {data.get('job_id')}")
        print(f"  Status: {data.get('status')}")
        
        if 'summary' in data:
            summary = data['summary']
            print(f"  Total Return: {summary.get('total_return', 'N/A')}%")
            print(f"  Sharpe Ratio: {summary.get('sharpe_ratio', 'N/A')}")
            print(f"  Total Trades: {summary.get('total_trades', 'N/A')}")
        
        return data.get('status')
    except Exception as e:
        print_error(f"Status check failed: {str(e)}")
        return None

def wait_for_completion(job_id, max_wait=300):
    """Wait for backtest to complete"""
    print_header("WAITING FOR BACKTEST TO COMPLETE")
    
    if not job_id:
        return False
    
    start_time = time.time()
    check_interval = 5
    
    print_info(f"Polling every {check_interval} seconds (max wait: {max_wait}s)")
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_BASE_URL}/backtest_status/{job_id}", timeout=10)
            response.raise_for_status()
            data = response.json()
            status = data.get('status')
            
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] Status: {status}")
            
            if status == "completed":
                print_success(f"Backtest completed in {elapsed} seconds")
                return True
            elif status == "failed":
                print_error("Backtest failed")
                return False
            
            time.sleep(check_interval)
        except Exception as e:
            print_error(f"Error checking status: {str(e)}")
            return False
    
    print_error(f"Backtest did not complete within {max_wait} seconds")
    return False

def test_get_results(job_id):
    """Test GET /backtest_results/{job_id} endpoint"""
    print_header("TEST 5: Get Backtest Results")
    
    if not job_id:
        print_error("No job ID provided, skipping results retrieval")
        return None
    
    try:
        print_info(f"Retrieving results for job: {job_id}")
        response = requests.get(f"{API_BASE_URL}/backtest_results/{job_id}", timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print_success("Results retrieved successfully")
        
        # Display summary
        summary = data.get('summary', {})
        print("\n" + "="*70)
        print("BACKTEST RESULTS SUMMARY")
        print("="*70)
        print(f"  Initial Capital:    ${summary.get('initial_capital', 0):,.2f}")
        print(f"  Final Value:        ${summary.get('final_value', 0):,.2f}")
        print(f"  Total Return:       {summary.get('total_return', 0):.2f}%")
        print(f"  CAGR:              {summary.get('cagr', 0):.2f}%")
        print(f"  Max Drawdown:      {summary.get('max_drawdown', 0):.2f}%")
        print(f"  Volatility:        {summary.get('volatility', 0):.2f}%")
        print(f"  Sharpe Ratio:      {summary.get('sharpe_ratio', 0):.2f}")
        print(f"  Sortino Ratio:     {summary.get('sortino_ratio', 0):.2f}")
        print(f"  Calmar Ratio:      {summary.get('calmar_ratio', 0):.2f}")
        print(f"  Total Trades:      {summary.get('total_trades', 0)}")
        print(f"  Winning Trades:    {summary.get('winning_trades', 0)}")
        print(f"  Losing Trades:     {summary.get('losing_trades', 0)}")
        print(f"  Win Rate:          {summary.get('win_rate', 0):.2f}%")
        print(f"  Profit Factor:     {summary.get('profit_factor', 0):.2f}")
        
        # Display sample trades
        trades = data.get('trades', [])
        if trades:
            print(f"\n  Sample Trades (showing first 3 of {len(trades)}):")
            for i, trade in enumerate(trades[:3], 1):
                print(f"    Trade {i}:")
                print(f"      Entry: {trade.get('Entry Date')} @ ${trade.get('Entry Price', 0):.2f}")
                print(f"      Exit:  {trade.get('Exit Date')} @ ${trade.get('Exit Price', 0):.2f}")
                print(f"      P&L: ${trade.get('P&L', 0):,.2f} ({trade.get('P&L %', 0):.2f}%)")
        
        # Save full results to file
        output_file = f"ibm_api_test_results_{job_id[:8]}.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n  Full results saved to: {output_file}")
        
        return data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 202:
            print_info("Backtest still running, results not available yet")
            return None
        else:
            print_error(f"HTTP error: {e}")
            return None
    except Exception as e:
        print_error(f"Get results failed: {str(e)}")
        return None

def test_list_backtests():
    """Test GET /list_backtests endpoint"""
    print_header("TEST 6: List All Backtests")
    
    try:
        response = requests.get(f"{API_BASE_URL}/list_backtests", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print_success("Backtest list retrieved successfully")
        print(f"  Total Jobs: {data.get('total', 0)}")
        
        jobs = data.get('jobs', [])
        if jobs:
            print("\n  Jobs:")
            for job in jobs[:5]:  # Show first 5
                print(f"    - {job.get('job_id')[:8]}... : {job.get('status')}")
                if 'summary' in job:
                    s = job['summary']
                    print(f"      Return: {s.get('total_return', 'N/A')}%, "
                          f"Sharpe: {s.get('sharpe_ratio', 'N/A')}, "
                          f"Trades: {s.get('num_trades', 'N/A')}")
        else:
            print("  No backtests found")
        
        return True
    except Exception as e:
        print_error(f"List backtests failed: {str(e)}")
        return False

def test_delete_backtest(job_id):
    """Test DELETE /backtest_results/{job_id} endpoint"""
    print_header("TEST 7: Delete Backtest Results")
    
    if not job_id:
        print_error("No job ID provided, skipping delete test")
        return False
    
    try:
        print_info(f"Deleting backtest: {job_id}")
        response = requests.delete(f"{API_BASE_URL}/backtest_results/{job_id}", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print_success("Backtest deleted successfully")
        print(f"  Message: {data.get('message')}")
        return True
    except Exception as e:
        print_error(f"Delete backtest failed: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print_header("BACKEND API TEST SUITE - IBM TEST SYMBOL")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Test Ticker: {TEST_TICKER}")
    print(f"Test Period: {TEST_START_DATE} to {TEST_END_DATE}")
    
    # Test 1: Health check
    if not test_health_check():
        print_error("\nBackend is not running. Please start it first:")
        print_info("  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Test 2: Root endpoint
    test_root_endpoint()
    
    # Test 3: Submit backtest
    job_id = test_submit_backtest()
    
    if not job_id:
        print_error("\nFailed to submit backtest. Cannot continue with remaining tests.")
        sys.exit(1)
    
    # Test 4: Check status (initial)
    status = test_check_status(job_id)
    
    # Wait for completion
    if status in ["queued", "running"]:
        completed = wait_for_completion(job_id)
        if completed:
            # Test 4 again: Check status (completed)
            test_check_status(job_id)
    
    # Test 5: Get results
    results = test_get_results(job_id)
    
    # Test 6: List all backtests
    test_list_backtests()
    
    # Test 7: Delete backtest (optional - comment out if you want to keep results)
    # test_delete_backtest(job_id)
    
    # Summary
    print_header("TEST SUMMARY")
    print_success("All API tests completed!")
    print(f"  Job ID: {job_id}")
    if results:
        print(f"  Backtest Status: Completed")
        print(f"  Total Return: {results.get('summary', {}).get('total_return', 'N/A')}%")
    else:
        print(f"  Backtest Status: Check manually")

if __name__ == "__main__":
    main()


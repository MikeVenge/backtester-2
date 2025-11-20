# Backend API Testing Guide

This guide shows how to test all backend API functions using IBM as a test symbol.

## Prerequisites

1. **Start the Backend Server**:
   ```bash
   # Set API key
   export ALPHAVANTAGE_API_KEY=your_api_key_here
   
   # Start backend
   ./run_backend.sh
   # OR
   python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Install Test Dependencies** (if not already installed):
   ```bash
   pip install requests
   ```

## Running the Test Suite

The test script (`test_api_cli.py`) tests all API endpoints:

```bash
python3 test_api_cli.py
```

## What Gets Tested

### 1. Health Check (`GET /health`)
- Verifies backend is running
- Checks API status

### 2. Root Endpoint (`GET /`)
- Tests basic API connectivity
- Returns API version info

### 3. Submit Backtest (`POST /run_backtest`)
- Submits a backtest job for IBM
- Strategy: Buy every 3 days, sell after 6 days
- Period: 2024-05-01 to 2025-05-01
- Returns job ID

### 4. Check Status (`GET /backtest_status/{job_id}`)
- Monitors backtest progress
- Shows current status (queued/running/completed)

### 5. Get Results (`GET /backtest_results/{job_id}`)
- Retrieves complete backtest results
- Displays performance metrics
- Shows sample trades
- Saves full results to JSON file

### 6. List Backtests (`GET /list_backtests`)
- Lists all backtest jobs
- Shows status and summary for each

### 7. Delete Backtest (`DELETE /backtest_results/{job_id}`)
- Deletes a backtest job (optional test)

## Test Configuration

The test uses the following configuration:

- **Ticker**: IBM
- **Period**: 2024-05-01 to 2025-05-01
- **Strategy**: Buy every 3 business days, sell after 6 days
- **Initial Capital**: $100,000
- **Position Size**: $10,000 per trade
- **Commission**: $1 per trade

## Expected Output

```
======================================================================
               BACKEND API TEST SUITE - IBM TEST SYMBOL
======================================================================

✓ Health check passed
✓ Root endpoint accessible
✓ Backtest job submitted successfully
  Job ID: 550e8400-e29b-41d4-a716-446655440000
  Status: queued

✓ Backtest completed in 45 seconds

✓ Results retrieved successfully
  Total Return: 12.34%
  Sharpe Ratio: 1.23
  Total Trades: 45
  ...
```

## Manual Testing

You can also test endpoints manually using `curl`:

### Health Check
```bash
curl http://localhost:8000/health
```

### Submit Backtest
```bash
curl -X POST http://localhost:8000/run_backtest \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "name": "IBM Test",
  "data": {
    "marketData": {
      "tickers": "IBM",
      "fields": ["open", "high", "low", "close", "volume"],
      "frequency": "daily",
      "startDate": "2024-05-01",
      "endDate": "2025-05-01",
      "includeDividends": true,
      "includeSplits": true
    },
    ...
  }
}
EOF
```

### Check Status
```bash
curl http://localhost:8000/backtest_status/{job_id}
```

### Get Results
```bash
curl http://localhost:8000/backtest_results/{job_id}
```

## Troubleshooting

### Backend Not Running
```
✗ Could not connect to http://localhost:8000
```
**Solution**: Start the backend server first (see Prerequisites)

### API Key Not Set
```
ValueError: AlphaVantage API key not provided
```
**Solution**: Set `ALPHAVANTAGE_API_KEY` environment variable

### Backtest Takes Too Long
The test waits up to 5 minutes for completion. If it takes longer:
- Check Railway logs (if deployed)
- Check backend logs for errors
- Verify AlphaVantage API is responding

### Connection Refused
```
Connection refused
```
**Solution**: 
- Verify backend is running on port 8000
- Check if port 8000 is already in use
- Try a different port: `--port 8001`

## Test Results

Test results are saved to:
- `ibm_api_test_results_{job_id}.json` - Full backtest results

## Next Steps

After testing locally:
1. Deploy backend to Railway
2. Update `API_BASE_URL` in `test_api_cli.py` to Railway URL
3. Run tests against production API
4. Deploy frontend to Vercel
5. Configure frontend to use Railway backend URL


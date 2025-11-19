# Quick Start Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Running the Backend

### Start the Server

```bash
# From the backend directory
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or from the project root:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Verify the Server is Running

Open your browser and visit: http://localhost:8000

You should see:
```json
{
  "message": "Backtester API is running",
  "version": "1.0.0",
  "status": "healthy"
}
```

## Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T12:00:00.000000",
  "active_backtests": 0
}
```

### 2. Submit a Backtest

```bash
curl -X POST http://localhost:8000/run_backtest \
  -H "Content-Type: application/json" \
  -d @backend/example_config.json
```

Expected response:
```json
{
  "status": "queued",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Backtest 'Simple Moving Average Strategy' has been queued for execution",
  "config_summary": {
    "name": "Simple Moving Average Strategy",
    "tickers": "AAPL,MSFT,GOOGL",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000.0
  }
}
```

Save the `job_id` from the response.

### 3. Check Backtest Status

```bash
curl http://localhost:8000/backtest_status/{job_id}
```

Replace `{job_id}` with the actual job ID from step 2.

Expected response (while running):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running"
}
```

Expected response (when completed):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "summary": {
    "total_return": 15.2,
    "cagr": 14.8,
    "sharpe_ratio": 1.35,
    ...
  }
}
```

### 4. Get Full Results

```bash
curl http://localhost:8000/backtest_results/{job_id}
```

This will return the complete backtest results including:
- Performance summary
- Equity curve
- All trades
- Current positions
- Benchmark comparison

### 5. List All Backtests

```bash
curl http://localhost:8000/list_backtests
```

Expected response:
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "summary": {
        "total_return": 15.2,
        "sharpe_ratio": 1.35,
        "num_trades": 45
      }
    }
  ],
  "total": 1
}
```

## Using with the Frontend

### 1. Start the Backend (as above)

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend

In a separate terminal:

```bash
npm install
npm run dev
```

The frontend should start on http://localhost:5173

### 3. Configure and Run Backtest

1. Open http://localhost:5173 in your browser
2. Fill out the configuration tabs
3. Click "Run Backtest"
4. The frontend will submit to the backend and poll for results

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

Then update the frontend API URL accordingly.

### Module Import Errors

If you get import errors, make sure you're running from the correct directory:

```bash
# From project root
python -m uvicorn backend.main:app --reload

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m uvicorn backend.main:app --reload
```

### CORS Errors

If the frontend can't connect, check the CORS settings in `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    ...
)
```

Add your frontend URL if it's different.

## Example: Using Python Requests

```python
import requests
import json
import time

# Load configuration
with open('backend/example_config.json', 'r') as f:
    config = json.load(f)

# Submit backtest
response = requests.post('http://localhost:8000/run_backtest', json=config)
job_id = response.json()['job_id']
print(f"Job ID: {job_id}")

# Poll for completion
while True:
    status_response = requests.get(f'http://localhost:8000/backtest_status/{job_id}')
    status = status_response.json()['status']
    print(f"Status: {status}")
    
    if status == 'completed':
        break
    elif status == 'failed':
        print("Backtest failed!")
        break
    
    time.sleep(2)

# Get results
results = requests.get(f'http://localhost:8000/backtest_results/{job_id}')
print(json.dumps(results.json(), indent=2))
```

## Next Steps

1. **Review the code**: Check out the modules in the `backend/` directory
2. **Read the docs**: See `backend/README.md` for detailed documentation
3. **Customize strategies**: Modify `backend/strategy.py` to add your logic
4. **Add AlphaVantage**: Integrate real market data from AlphaVantage MCP
5. **Deploy**: Set up production deployment with proper database

## Getting Help

- Check the logs in the terminal where the server is running
- Review `BACKEND_SPECIFICATION.md` for detailed behavior
- Read `BACKEND_IMPLEMENTATION_SUMMARY.md` for architecture overview

## Development Mode

The server runs with `--reload` flag, which automatically restarts when you make code changes. This is great for development but should be disabled in production.

For production:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```


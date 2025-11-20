#!/bin/bash
# Script to start the backend server for testing

echo "Starting Backtester Backend API..."
echo "Make sure ALPHAVANTAGE_API_KEY is set:"
echo "  export ALPHAVANTAGE_API_KEY=your_key_here"
echo ""

cd "$(dirname "$0")"

# Check if API key is set
if [ -z "$ALPHAVANTAGE_API_KEY" ]; then
    echo "⚠️  Warning: ALPHAVANTAGE_API_KEY not set"
    echo "   Set it with: export ALPHAVANTAGE_API_KEY=your_key"
    echo ""
fi

# Start the backend
echo "Starting uvicorn server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000


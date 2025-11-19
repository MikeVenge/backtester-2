# Project Structure

This document describes the restructured codebase with separate frontend and backend directories.

## Directory Structure

```
backtester-2/
├── frontend/                    # React frontend application
│   ├── src/                     # React source code
│   │   ├── components/          # React components
│   │   │   ├── ConfigurationManager.jsx
│   │   │   ├── MarketData.jsx
│   │   │   ├── StrategyDefinition.jsx
│   │   │   └── ...
│   │   ├── App.jsx              # Main app component
│   │   ├── main.jsx             # Entry point
│   │   └── index.css            # Global styles
│   ├── index.html               # HTML template
│   ├── package.json             # Frontend dependencies
│   ├── vite.config.js           # Vite configuration
│   ├── vercel.json              # Vercel deployment config
│   ├── .gitignore               # Frontend gitignore
│   ├── .env.example             # Environment variables example
│   └── README.md                # Frontend documentation
│
├── backend/                     # FastAPI backend application
│   ├── __init__.py              # Python package marker
│   ├── main.py                  # FastAPI application entry point
│   ├── models.py                # Pydantic models
│   ├── backtest_engine.py        # Core backtest engine
│   ├── data_fetcher.py          # Market data fetching
│   ├── portfolio.py             # Portfolio management
│   ├── strategy.py              # Strategy execution
│   ├── performance.py           # Performance metrics
│   ├── utils.py                 # Utility functions
│   ├── av_mcp_client.py         # AlphaVantage client
│   ├── simple_strategies.py     # Simple strategy handlers
│   ├── requirements.txt          # Python dependencies
│   ├── API.md                   # API documentation
│   ├── README.md                # Backend documentation
│   └── RAILWAY_DEPLOYMENT.md    # Railway deployment guide
│
├── Procfile                      # Railway start command
├── railway.json                  # Railway configuration
├── requirements.txt              # Backend dependencies (for Railway)
├── runtime.txt                   # Python version for Railway
├── README.md                     # Project root README
├── BACKEND_SPECIFICATION.md     # Backend specification
├── BACKEND_IMPLEMENTATION_SUMMARY.md  # Implementation summary
└── PROJECT_STRUCTURE.md          # This file
```

## Deployment

### Frontend → Vercel

- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variable**: `VITE_API_URL` (set to Railway backend URL)

### Backend → Railway

- **Root Directory**: `/` (root)
- **Build**: Auto-detects Python from `requirements.txt`
- **Start Command**: From `Procfile` (`uvicorn backend.main:app`)
- **Environment Variables**: 
  - `ALPHAVANTAGE_API_KEY` (required)
  - `FRONTEND_URL` (optional, for CORS)
  - `PORT` (auto-set by Railway)

## Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

### Backend Development

```bash
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`

### Environment Variables

**Frontend** (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
```

**Backend** (set in Railway or `.env`):
```env
ALPHAVANTAGE_API_KEY=your_key_here
FRONTEND_URL=http://localhost:5173
```

## Key Files

### Frontend
- `frontend/package.json` - Dependencies and scripts
- `frontend/vite.config.js` - Vite build configuration
- `frontend/vercel.json` - Vercel deployment configuration
- `frontend/src/components/ConfigurationManager.jsx` - Main component with API calls

### Backend
- `backend/main.py` - FastAPI application
- `backend/requirements.txt` - Python dependencies
- `Procfile` - Railway start command
- `railway.json` - Railway configuration

## API Communication

The frontend communicates with the backend via HTTP:

- **Development**: `http://localhost:8000` (configured via `VITE_API_URL`)
- **Production**: Railway backend URL (set in Vercel environment variables)

All API calls use the `VITE_API_URL` environment variable, making it easy to switch between development and production.

## Notes

- The frontend and backend are completely independent and can be deployed separately
- The frontend uses Vite's environment variable prefix `VITE_` for client-side variables
- The backend uses standard environment variables (no prefix needed)
- Both directories have their own `.gitignore` files
- Root-level `requirements.txt` and `Procfile` are for Railway deployment only


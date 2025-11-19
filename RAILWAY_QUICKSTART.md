# Railway Deployment Quick Start

## Quick Deploy Steps

1. **Push to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Connect to Railway**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `backtester-2` repository
   - **IMPORTANT**: In Settings → Source → Root Directory, leave it **empty** or set to `/` (NOT `/backend`)

3. **Set Environment Variables**
   In Railway dashboard → Variables tab:
   ```
   ALPHAVANTAGE_API_KEY=your_api_key_here
   FRONTEND_URL=https://your-frontend-url.com  (optional)
   ```

4. **Deploy**
   - Railway will auto-detect Python and deploy
   - Wait for build to complete
   - Get your API URL from Railway dashboard

5. **Test**
   ```bash
   curl https://your-railway-url.railway.app/health
   ```

## Required Environment Variables

- `ALPHAVANTAGE_API_KEY` (required) - Your AlphaVantage API key
- `FRONTEND_URL` (optional) - Frontend URL for CORS, comma-separated
- `PORT` (auto-set by Railway) - Server port

## Files Created for Railway

- `Procfile` - Defines how to start the app (`uvicorn backend.main:app`)
- `railway.json` - Railway configuration
- `runtime.txt` - Python version specification
- `requirements.txt` - Python dependencies (in root, copied from `backend/requirements.txt`)
- `backend/RAILWAY_DEPLOYMENT.md` - Full deployment guide

## Backend Subdirectory

The backend code is in `/backend` directory. Railway handles this automatically:
- `requirements.txt` is in root (Railway looks here)
- `Procfile` uses `backend.main:app` (Python finds the backend package)
- No additional Railway settings needed!

## Troubleshooting

- **Build fails**: Check Railway logs, verify `requirements.txt` exists
- **CORS errors**: Add frontend URL to `FRONTEND_URL` env var
- **API errors**: Verify `ALPHAVANTAGE_API_KEY` is set correctly

For detailed instructions, see `backend/RAILWAY_DEPLOYMENT.md`


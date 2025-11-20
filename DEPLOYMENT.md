# Deployment Guide

This guide walks you through deploying both the backend (Railway) and frontend (Vercel).

## Prerequisites

- GitHub repository pushed (✅ Done)
- Railway account: https://railway.app
- Vercel account: https://vercel.com
- AlphaVantage API key: https://www.alphavantage.co/support/#api-key

## Step 1: Deploy Backend to Railway

### 1.1 Connect Repository to Railway

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `backtester-2` repository
5. Railway will detect it's a Python project

### 1.2 Configure Settings

**Root Directory:**
- Go to **Settings → Source → Root Directory**
- Leave it **empty** or set to `/` (NOT `/backend`)
- Railway needs to find `Procfile` and `requirements.txt` in root

### 1.3 Set Environment Variables

Go to **Variables** tab and add:

```
ALPHAVANTAGE_API_KEY=your_api_key_here
FRONTEND_URL=https://your-frontend.vercel.app
```

**Note**: You'll update `FRONTEND_URL` after deploying the frontend.

### 1.4 Deploy

- Railway will automatically deploy when you connect the repo
- Wait for the build to complete (check the Deployments tab)
- Once deployed, go to **Settings → Networking**
- Copy your **Public Domain** (e.g., `backtester-2-production.up.railway.app`)

### 1.5 Test Backend

```bash
curl https://your-railway-url.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "active_backtests": 0
}
```

## Step 2: Deploy Frontend to Vercel

### 2.1 Connect Repository to Vercel

1. Go to https://vercel.com
2. Click **"Add New Project"**
3. Import your `backtester-2` repository
4. Click **"Import"**

### 2.2 Configure Project Settings

**Framework Preset:** Vite (should auto-detect)

**Root Directory:** `frontend`

**Build Settings:**
- **Build Command**: `npm run build` (auto-filled)
- **Output Directory**: `dist` (auto-filled)
- **Install Command**: `npm install` (auto-filled)

### 2.3 Set Environment Variables

Click **"Environment Variables"** and add:

```
VITE_API_URL=https://your-railway-backend-url.railway.app
```

Replace `your-railway-backend-url.railway.app` with your actual Railway backend URL from Step 1.4.

### 2.4 Deploy

1. Click **"Deploy"**
2. Wait for the build to complete
3. Once deployed, Vercel will provide a URL (e.g., `backtester-2.vercel.app`)

### 2.5 Update Backend CORS

Go back to Railway and update the `FRONTEND_URL` environment variable:

```
FRONTEND_URL=https://your-frontend.vercel.app
```

Replace with your actual Vercel frontend URL.

## Step 3: Verify Deployment

### Test Frontend
1. Open your Vercel URL in a browser
2. The frontend should load
3. Try configuring a backtest

### Test Backend Connection
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try running a backtest
4. Check that API calls go to your Railway backend URL

## Troubleshooting

### Backend Issues

**502 Bad Gateway:**
- Check Railway logs (Deployments → View Logs)
- Verify `ALPHAVANTAGE_API_KEY` is set
- Check that Root Directory is `/` (not `/backend`)

**CORS Errors:**
- Verify `FRONTEND_URL` in Railway matches your Vercel URL exactly
- Include `https://` protocol
- Check Railway logs for CORS-related errors

### Frontend Issues

**API Connection Errors:**
- Verify `VITE_API_URL` in Vercel matches your Railway backend URL
- Check browser console for errors
- Ensure Railway backend is running (check Railway dashboard)

**Build Errors:**
- Check Vercel build logs
- Verify `frontend/` directory structure
- Ensure `package.json` exists in `frontend/`

## Quick Reference

### Backend (Railway)
- **Root Directory**: `/` (root)
- **Environment Variables**: 
  - `ALPHAVANTAGE_API_KEY` (required)
  - `FRONTEND_URL` (your Vercel URL)
- **Public Domain**: Found in Settings → Networking

### Frontend (Vercel)
- **Root Directory**: `frontend`
- **Environment Variables**:
  - `VITE_API_URL` (your Railway backend URL)
- **Deployment URL**: Provided after deployment

## URLs After Deployment

- **Backend API**: `https://backtester-2-production.up.railway.app`
- **Frontend**: `https://backtester-2.vercel.app`
- **Backend Health Check**: `https://backtester-2-production.up.railway.app/health`
- **Backend API Docs**: `https://backtester-2-production.up.railway.app/docs`

## Next Steps

1. ✅ Backend deployed to Railway
2. ✅ Frontend deployed to Vercel
3. ✅ Environment variables configured
4. ✅ CORS configured
5. 🎉 Your backtester is live!


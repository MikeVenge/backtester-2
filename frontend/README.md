# Backtester Frontend

React-based frontend for the Backtester application. This frontend provides a user interface for configuring and running backtests.

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **CSS** - Styling

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Configuration

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000
```

**For Production (Vercel):**
- Set `VITE_API_URL` in Vercel environment variables
- Use your Railway backend URL: `https://your-backend.railway.app`

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ConfigurationManager.jsx
│   │   ├── MarketData.jsx
│   │   ├── StrategyDefinition.jsx
│   │   └── ...
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── index.html              # HTML template
├── package.json            # Dependencies
├── vite.config.js          # Vite configuration
└── vercel.json             # Vercel deployment config
```

## Deployment to Vercel

### Option 1: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Follow the prompts
```

### Option 2: GitHub Integration

1. Push your code to GitHub
2. Go to [Vercel Dashboard](https://vercel.com/dashboard)
3. Click "New Project"
4. Import your GitHub repository
5. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
6. Add Environment Variable:
   - `VITE_API_URL` = `https://your-backend.railway.app`
7. Deploy

### Option 3: Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import from GitHub
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variables:
   - `VITE_API_URL` = Your Railway backend URL
6. Deploy

## Environment Variables for Vercel

In Vercel dashboard → Project Settings → Environment Variables:

- **`VITE_API_URL`** (required): Your backend API URL
  - Development: `http://localhost:8000`
  - Production: `https://backtester-2-production.up.railway.app` (or your Railway backend URL)

## Features

- **Configuration Management**: Save, load, and manage multiple backtest configurations
- **Form Sections**: 
  - Market Data
  - Strategy Definition
  - Portfolio & Risk Settings
  - Trading & Execution
  - MTM Settings
  - Rebalancing Rules
  - Output & Evaluation
  - Implementation Details
- **Run Backtests**: Submit configurations to the backend API
- **Local Storage**: Configurations are saved in browser localStorage

## API Integration

The frontend communicates with the backend API:

- **POST** `/run_backtest` - Submit a backtest configuration
- **GET** `/backtest_status/{job_id}` - Check backtest status
- **GET** `/backtest_results/{job_id}` - Get backtest results
- **GET** `/list_backtests` - List all backtests
- **DELETE** `/backtest_results/{job_id}` - Delete backtest results

See `backend/API.md` for complete API documentation.

## Troubleshooting

### CORS Errors

If you see CORS errors:
1. Ensure your backend has `FRONTEND_URL` environment variable set to your Vercel URL
2. Check that the backend CORS middleware is configured correctly

### API Connection Errors

1. Verify `VITE_API_URL` is set correctly
2. Check that the backend is running and accessible
3. Verify the backend URL includes `https://` for production

### Build Errors

1. Ensure all dependencies are installed: `npm install`
2. Check Node.js version: `node --version` (should be 18+)
3. Clear cache and rebuild: `rm -rf node_modules dist && npm install && npm run build`

## Development Notes

- The frontend uses Vite's environment variable prefix `VITE_` for client-side variables
- All API calls use the `VITE_API_URL` environment variable
- LocalStorage is used for configuration persistence (client-side only)


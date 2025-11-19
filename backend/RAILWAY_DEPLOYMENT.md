# Railway Deployment Guide

This guide explains how to deploy the Backtester backend to Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. An AlphaVantage API key (get one at https://www.alphavantage.co/support/#api-key)

## Important: Project Structure

**Note**: This project has a monorepo structure:
- **Frontend**: Located in `/frontend` directory (deploy to Vercel)
- **Backend**: Located in `/backend` directory (deploy to Railway)

For Railway backend deployment:
- ✅ `requirements.txt` is in the root directory (copied from `backend/requirements.txt`)
- ✅ `Procfile` references `backend.main:app` which Python will resolve correctly
- ✅ Railway will install dependencies from root `requirements.txt`
- ✅ The `backend` directory is a Python package (has `__init__.py`)

**No additional Railway configuration needed** - Railway will automatically:
- Detect Python from `requirements.txt` in root
- Install all dependencies
- Run the app using the `Procfile` command

## Deployment Steps

### 1. Connect Your Repository

1. Log in to Railway
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `backtester-2` repository
5. Railway will automatically detect it's a Python project

**⚠️ IMPORTANT - Root Directory Setting:**
- Go to **Settings → Source → Root Directory**
- Leave it **empty** or set to `/` (root directory)
- **DO NOT** set it to `/backend`
- Railway needs to find `Procfile`, `requirements.txt`, and `railway.json` in the root directory
- The `uvicorn backend.main:app` command runs from root and imports the `backend` module

### 2. Configure Environment Variables

In the Railway project dashboard:

1. Go to the "Variables" tab
2. Add the following environment variables:

   - **ALPHAVANTAGE_API_KEY**: Your AlphaVantage API key (required)
   - **FRONTEND_URL**: Your frontend URL(s) for CORS (optional, comma-separated)
     - Example: `https://your-frontend.railway.app,https://your-frontend.vercel.app`
     - If not set, defaults to `http://localhost:5173`

### 3. Configure Build Settings

Railway will automatically:
- Detect Python from `requirements.txt` in the root directory
- Install dependencies from `requirements.txt`
- Use the `Procfile` to start the application (which references `backend.main:app`)
- Set the `PORT` environment variable automatically
- Set the Python path correctly so `backend` module can be imported

**Note**: Since the backend is in `/backend`, Railway will:
- Run from the repository root directory
- Python will automatically find the `backend` package (because it has `__init__.py`)
- The `uvicorn backend.main:app` command will work correctly

### 4. Deploy

1. Railway will automatically deploy when you push to the main branch
2. Or click "Deploy" in the Railway dashboard
3. Wait for the build to complete
4. Your API will be available at the Railway-provided URL

### 5. Get Your API URL

After deployment, Railway provides two types of domains:

**Internal Domain** (for service-to-service communication):
- Format: `backtester-2.railway.internal`
- Only accessible from other Railway services in the same project
- Use this if you have other Railway services that need to communicate with the backend
- No authentication required between Railway services

**Public Domain** (for external access):
1. Go to your service in Railway
2. Click on the "Settings" tab
3. Scroll to "Networking" section
4. Find your public domain (e.g., `backtester-2-production.up.railway.app`)
5. Or generate a custom domain if needed
6. Use this URL as your API base URL for frontend/external access

**Which one to use:**
- **Frontend/External access**: Use the public domain (e.g., `https://backtester-2-production.up.railway.app`)
- **Railway service-to-service**: Use internal domain (e.g., `http://backtester-2.railway.internal`)

## Testing the Deployment

Once deployed, test your API:

**Using Public Domain** (from your computer):
```bash
# Health check
curl https://your-railway-url.railway.app/health

# Should return:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-01T00:00:00",
#   "active_backtests": 0
# }
```

**Using Internal Domain** (from another Railway service):
```bash
# Health check from within Railway
curl http://backtester-2.railway.internal/health
```

**Note**: The internal domain (`backtester-2.railway.internal`) is only accessible from other Railway services. For external access (frontend, API testing tools), use the public domain.

## Updating the Frontend

After deploying to Railway, update your frontend to use the Railway API URL:

1. Update your frontend API base URL to point to your Railway backend
2. If your frontend is on a different domain, add it to the `FRONTEND_URL` environment variable in Railway

## Monitoring

Railway provides:
- **Logs**: View real-time logs in the Railway dashboard
- **Metrics**: CPU, memory, and network usage
- **Deployments**: History of all deployments

## Troubleshooting

### Build Fails

- Check that `requirements.txt` is in the root directory
- Verify all dependencies are listed correctly
- Check Railway logs for specific error messages

### API Returns CORS Errors

- Add your frontend URL to the `FRONTEND_URL` environment variable
- Ensure the URL format is correct (include protocol: `https://`)

### AlphaVantage API Errors

- Verify `ALPHAVANTAGE_API_KEY` is set correctly
- Check that the API key is valid and has not exceeded rate limits
- Review Railway logs for specific error messages

### Port Already in Use

- Railway automatically sets the `PORT` environment variable
- Do not hardcode a port number
- The `Procfile` uses `$PORT` which Railway provides

### 502 Bad Gateway Error

If you see a 502 error when accessing your public domain:

1. **Check Deployment Status**:
   - Go to Railway dashboard → Deployments tab
   - Verify the latest deployment completed successfully (green checkmark)
   - If deployment failed, check the build logs

2. **Check Application Logs**:
   - Go to Railway dashboard → Your Service → Logs tab
   - Look for startup errors, import errors, or missing dependencies
   - Common issues:
     - Missing `ALPHAVANTAGE_API_KEY` environment variable
     - Import errors (check that `backend` module can be found)
     - Port binding issues

3. **Verify Environment Variables**:
   - Go to Variables tab
   - Ensure `ALPHAVANTAGE_API_KEY` is set
   - Railway automatically sets `PORT` - don't override it

4. **Check Root Directory**:
   - Settings → Source → Root Directory should be `/` or empty
   - NOT `/backend`

5. **Verify Files Exist**:
   - `Procfile` should be in root directory
   - `requirements.txt` should be in root directory
   - `backend/` directory should contain `main.py` and `__init__.py`

## File Structure

The following files are used for Railway deployment:

- **`Procfile`**: Defines the command to start the application
- **`railway.json`**: Railway-specific configuration
- **`requirements.txt`**: Python dependencies
- **`backend/main.py`**: FastAPI application entry point
- **`.env.example`**: Example environment variables (for reference)

## Production Considerations

1. **Database**: Currently, backtest results are stored in memory. For production, consider:
   - PostgreSQL (Railway offers managed PostgreSQL)
   - Redis for caching
   - File-based storage for persistence

2. **Rate Limiting**: Consider adding rate limiting to prevent abuse

3. **Authentication**: Add API authentication if exposing publicly

4. **Error Handling**: Ensure all errors are properly logged and handled

5. **Scaling**: Railway can auto-scale based on traffic

## Support

For Railway-specific issues, check:
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

For application-specific issues, check the backend logs in Railway dashboard.


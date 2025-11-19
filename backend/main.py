from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .models import BacktestRequest
from .backtest_engine import BacktestEngine
from .utils import validate_backtest_config
import uvicorn
import json
import os
import logging
import uuid
from typing import Dict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Backtester Backend", version="1.0.0")

# Configure CORS - allow requests from frontend
# In production, set FRONTEND_URL environment variable or use Railway's domain
frontend_urls = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_urls + ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for backtest results (in production, use a database)
backtest_results: Dict[str, Dict] = {}
backtest_status: Dict[str, str] = {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Backtester API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_backtests": len([s for s in backtest_status.values() if s == "running"])
    }


@app.post("/run_backtest")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Submit a backtest job for execution
    
    Args:
        request: Backtest configuration request
        background_tasks: FastAPI background tasks
    
    Returns:
        Job submission confirmation with job ID
    """
    logger.info(f"Received backtest request: {request.name}")
    
    # Convert Pydantic model to dict for processing
    config_dict = {
        'marketData': request.data.marketData.dict() if request.data.marketData else {},
        'strategy': request.data.strategy.dict() if request.data.strategy else {},
        'portfolioRisk': request.data.portfolioRisk.dict() if request.data.portfolioRisk else {},
        'tradingExecution': request.data.tradingExecution.dict() if request.data.tradingExecution else {},
        'mtm': request.data.mtm.dict() if request.data.mtm else {},
        'rebalancing': request.data.rebalancing.dict() if request.data.rebalancing else {},
        'output': request.data.output.dict() if request.data.output else {},
        'implementation': request.data.implementation.dict() if request.data.implementation else {}
    }
    
    # Validate configuration
    is_valid, error_msg = validate_backtest_config(config_dict)
    if not is_valid:
        logger.error(f"Invalid configuration: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Initialize status
    backtest_status[job_id] = "queued"
    
    # Add backtest to background tasks
    background_tasks.add_task(execute_backtest, job_id, config_dict, request.name)
    
    logger.info(f"Backtest job queued: {job_id}")
    
    return {
        "status": "queued",
        "job_id": job_id,
        "message": f"Backtest '{request.name}' has been queued for execution",
        "config_summary": {
            "name": request.name,
            "tickers": config_dict['marketData'].get('tickers'),
            "start_date": config_dict['marketData'].get('startDate'),
            "end_date": config_dict['marketData'].get('endDate'),
            "initial_capital": config_dict['portfolioRisk'].get('initialCapital')
        }
    }


@app.get("/backtest_status/{job_id}")
async def get_backtest_status(job_id: str):
    """
    Get the status of a backtest job
    
    Args:
        job_id: Backtest job ID
    
    Returns:
        Job status information
    """
    if job_id not in backtest_status:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    
    status = backtest_status[job_id]
    
    response = {
        "job_id": job_id,
        "status": status
    }
    
    # If completed, include summary
    if status == "completed" and job_id in backtest_results:
        results = backtest_results[job_id]
        response["summary"] = results.get("summary", {})
    
    return response


@app.get("/backtest_results/{job_id}")
async def get_backtest_results(job_id: str):
    """
    Get the full results of a completed backtest
    
    Args:
        job_id: Backtest job ID
    
    Returns:
        Complete backtest results
    """
    if job_id not in backtest_status:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    
    status = backtest_status[job_id]
    
    if status == "running" or status == "queued":
        raise HTTPException(status_code=202, detail="Backtest is still running")
    
    if status == "failed":
        raise HTTPException(status_code=500, detail="Backtest execution failed")
    
    if job_id not in backtest_results:
        raise HTTPException(status_code=404, detail="Backtest results not found")
    
    return backtest_results[job_id]


@app.delete("/backtest_results/{job_id}")
async def delete_backtest_results(job_id: str):
    """
    Delete backtest results
    
    Args:
        job_id: Backtest job ID
    
    Returns:
        Deletion confirmation
    """
    if job_id not in backtest_status:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    
    # Remove from storage
    if job_id in backtest_results:
        del backtest_results[job_id]
    if job_id in backtest_status:
        del backtest_status[job_id]
    
    return {
        "status": "success",
        "message": f"Backtest {job_id} deleted"
    }


@app.get("/list_backtests")
async def list_backtests():
    """
    List all backtest jobs
    
    Returns:
        List of all backtest jobs with their status
    """
    jobs = []
    for job_id, status in backtest_status.items():
        job_info = {
            "job_id": job_id,
            "status": status
        }
        
        if status == "completed" and job_id in backtest_results:
            results = backtest_results[job_id]
            job_info["summary"] = {
                "total_return": results.get("summary", {}).get("total_return"),
                "sharpe_ratio": results.get("summary", {}).get("sharpe_ratio"),
                "num_trades": results.get("summary", {}).get("total_trades")
            }
        
        jobs.append(job_info)
    
    return {"jobs": jobs, "total": len(jobs)}


async def execute_backtest(job_id: str, config: Dict, name: str):
    """
    Background task to execute backtest
    
    Args:
        job_id: Backtest job ID
        config: Backtest configuration
        name: Backtest name
    """
    try:
        logger.info(f"Starting backtest execution: {job_id}")
        backtest_status[job_id] = "running"
        
        # Initialize backtest engine
        engine = BacktestEngine(config)
        
        # Run backtest
        results = await engine.run()
        
        # Add metadata
        results['job_id'] = job_id
        results['name'] = name
        results['completed_at'] = datetime.now().isoformat()
        
        # Store results
        backtest_results[job_id] = results
        backtest_status[job_id] = "completed"
        
        logger.info(f"Backtest completed successfully: {job_id}")
        
    except Exception as e:
        logger.error(f"Backtest failed: {job_id} - {str(e)}", exc_info=True)
        backtest_status[job_id] = "failed"
        backtest_results[job_id] = {
            "status": "failed",
            "error": str(e),
            "job_id": job_id
        }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)


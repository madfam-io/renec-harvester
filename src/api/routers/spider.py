"""
Spider control API endpoints.
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Optional

from ..models import SpiderConfig, SpiderResponse, SpiderStatus
from ..spider_manager import SpiderManager

router = APIRouter()


@router.post("/spider/start", response_model=SpiderResponse)
async def start_spider(config: SpiderConfig, request: Request):
    """Start the scraping spider with given configuration."""
    try:
        spider_manager: SpiderManager = request.app.state.spider_manager
        
        if spider_manager.is_running():
            raise HTTPException(
                status_code=400,
                detail="Spider is already running. Stop it first."
            )
        
        success = await spider_manager.start(config)
        
        if success:
            return SpiderResponse(
                success=True,
                message="Spider started successfully",
                status=SpiderStatus.RUNNING,
                config=config
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to start spider"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spider/stop", response_model=SpiderResponse)
async def stop_spider(request: Request):
    """Stop the running spider."""
    try:
        spider_manager: SpiderManager = request.app.state.spider_manager
        
        if not spider_manager.is_running():
            raise HTTPException(
                status_code=400,
                detail="No spider is currently running"
            )
        
        success = await spider_manager.stop()
        
        if success:
            return SpiderResponse(
                success=True,
                message="Spider stopped successfully",
                status=SpiderStatus.IDLE
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to stop spider"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spider/pause", response_model=SpiderResponse)  
async def pause_spider(request: Request):
    """Pause the running spider."""
    try:
        spider_manager: SpiderManager = request.app.state.spider_manager
        
        if not spider_manager.is_running():
            raise HTTPException(
                status_code=400,
                detail="No spider is currently running"
            )
        
        success = await spider_manager.pause()
        
        if success:
            return SpiderResponse(
                success=True,
                message="Spider paused successfully",
                status=SpiderStatus.PAUSED
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to pause spider"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spider/resume", response_model=SpiderResponse)
async def resume_spider(request: Request):
    """Resume a paused spider."""
    try:
        spider_manager: SpiderManager = request.app.state.spider_manager
        
        if spider_manager.get_status() != SpiderStatus.PAUSED:
            raise HTTPException(
                status_code=400,
                detail="Spider is not currently paused"
            )
        
        success = await spider_manager.resume()
        
        if success:
            return SpiderResponse(
                success=True,
                message="Spider resumed successfully", 
                status=SpiderStatus.RUNNING
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to resume spider"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spider/reset", response_model=SpiderResponse)
async def reset_spider(request: Request):
    """Reset spider state and clear any cached data."""
    try:
        spider_manager: SpiderManager = request.app.state.spider_manager
        
        success = await spider_manager.reset()
        
        if success:
            return SpiderResponse(
                success=True,
                message="Spider reset successfully",
                status=SpiderStatus.IDLE
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset spider"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spider/status", response_model=SpiderResponse)
async def get_spider_status(request: Request):
    """Get current spider status and configuration."""
    try:
        spider_manager: SpiderManager = request.app.state.spider_manager
        
        status = spider_manager.get_status()
        config = spider_manager.get_config()
        
        return SpiderResponse(
            success=True,
            message="Status retrieved successfully",
            status=status,
            config=config
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
Statistics and monitoring API endpoints.
"""
from fastapi import APIRouter, Request
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil
import time

from ..models import SpiderStats, SystemHealth
from ..spider_manager import SpiderManager

router = APIRouter()


@router.get("/stats", response_model=SpiderStats)
async def get_spider_stats(request: Request):
    """Get current spider statistics and performance metrics."""
    try:
        spider_manager: SpiderManager = request.app.state.spider_manager
        return spider_manager.get_stats()
    except Exception as e:
        # Return default stats if error
        return SpiderStats()


@router.get("/health", response_model=SystemHealth)
async def get_system_health():
    """Get system health status including database, Redis, and resources."""
    health = SystemHealth()
    
    try:
        # Check memory usage
        memory = psutil.virtual_memory()
        health.memory_usage = memory.percent
        
        # Check disk usage
        disk = psutil.disk_usage('/')
        health.disk_usage = (disk.used / disk.total) * 100
        
        # TODO: Add actual database and Redis health checks
        health.database = "healthy"
        health.redis = "healthy"
        health.spider = "idle"
        
    except Exception as e:
        print(f"Health check error: {e}")
    
    return health


@router.get("/metrics/history")
async def get_metrics_history(hours: int = 24):
    """Get historical performance metrics."""
    try:
        # Mock data for now - replace with actual metrics collection
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Generate mock data points every 5 minutes
        data_points = []
        current_time = start_time
        
        while current_time <= end_time:
            data_points.append({
                "timestamp": current_time.isoformat(),
                "requests": 45 + (hash(str(current_time)) % 20),  # Mock requests
                "items": 12 + (hash(str(current_time)) % 8),      # Mock items
                "errors": max(0, (hash(str(current_time)) % 5) - 3),  # Mock errors
                "response_time": 150 + (hash(str(current_time)) % 100)  # Mock response time
            })
            current_time += timedelta(minutes=5)
        
        return {
            "data": data_points,
            "period": f"{hours} hours",
            "total_points": len(data_points)
        }
    
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/metrics/components")
async def get_component_metrics():
    """Get per-component scraping progress and statistics."""
    try:
        # Mock component data - replace with actual database queries
        components = [
            {
                "name": "EC Standards", 
                "scraped": 1250,
                "total": 1500, 
                "last_updated": datetime.now().isoformat(),
                "success_rate": 94.5,
                "avg_response_time": 145
            },
            {
                "name": "Certificadores",
                "scraped": 890, 
                "total": 1200,
                "last_updated": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "success_rate": 97.8,
                "avg_response_time": 132
            },
            {
                "name": "Evaluation Centers",
                "scraped": 450,
                "total": 800,
                "last_updated": (datetime.now() - timedelta(minutes=32)).isoformat(), 
                "success_rate": 89.2,
                "avg_response_time": 178
            },
            {
                "name": "Courses",
                "scraped": 2100,
                "total": 3500,
                "last_updated": (datetime.now() - timedelta(minutes=8)).isoformat(),
                "success_rate": 92.1,
                "avg_response_time": 156
            },
            {
                "name": "Sectors", 
                "scraped": 75,
                "total": 100,
                "last_updated": (datetime.now() - timedelta(hours=2)).isoformat(),
                "success_rate": 100.0,
                "avg_response_time": 98
            }
        ]
        
        return {
            "components": components,
            "last_updated": datetime.now().isoformat(),
            "total_progress": sum(c["scraped"] for c in components) / sum(c["total"] for c in components) * 100
        }
    
    except Exception as e:
        return {"error": str(e), "components": []}


@router.get("/metrics/errors")
async def get_error_metrics(limit: int = 50):
    """Get recent error statistics and details."""
    try:
        # Mock error data - replace with actual error logging
        errors = [
            {
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "type": "HTTP_ERROR",
                "code": "404",
                "url": "https://conocer.gob.mx/RENEC/controlador.do?comp=EC&ec=123",
                "message": "Page not found",
                "count": 3
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "type": "TIMEOUT_ERROR", 
                "code": "TIMEOUT",
                "url": "https://conocer.gob.mx/RENEC/controlador.do?comp=CERT&id=456",
                "message": "Request timeout after 30 seconds",
                "count": 1
            },
            {
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "type": "PARSING_ERROR",
                "code": "PARSE_FAILED",
                "url": "https://conocer.gob.mx/RENEC/controlador.do?comp=COURSE&id=789", 
                "message": "Failed to extract course data",
                "count": 2
            }
        ]
        
        return {
            "errors": errors[:limit],
            "total_errors": len(errors),
            "error_rate": 2.1,  # Mock error rate percentage
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e), "errors": []}
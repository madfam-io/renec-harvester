"""System health check utilities."""

import os
from typing import Dict, Any

import psycopg2
import redis
from structlog import get_logger

logger = get_logger()


def check_system_health() -> Dict[str, Any]:
    """Check health status of all system components."""
    health_status = {
        "database": _check_database(),
        "redis": _check_redis(),
        "filesystem": _check_filesystem(),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
    
    return health_status


def _check_database() -> Dict[str, Any]:
    """Check PostgreSQL database health."""
    status = {
        "healthy": False,
        "status": "Unknown",
        "message": "",
        "url": os.getenv("DATABASE_URL", "Not configured"),
    }
    
    try:
        # Parse connection string
        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            status["status"] = "Not configured"
            status["message"] = "DATABASE_URL not set"
            return status
        
        # Try to connect
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        status["healthy"] = True
        status["status"] = "Connected"
        status["message"] = "PostgreSQL is running"
        
    except psycopg2.OperationalError as e:
        status["status"] = "Connection failed"
        status["message"] = str(e).split("\n")[0]
    except Exception as e:
        status["status"] = "Error"
        status["message"] = str(e)
    
    return status


def _check_redis() -> Dict[str, Any]:
    """Check Redis health."""
    status = {
        "healthy": False,
        "status": "Unknown",
        "message": "",
        "url": os.getenv("REDIS_URL", "Not configured"),
    }
    
    try:
        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url:
            status["status"] = "Not configured"
            status["message"] = "REDIS_URL not set"
            return status
        
        # Try to connect
        r = redis.from_url(redis_url)
        r.ping()
        
        # Get info
        info = r.info()
        status["healthy"] = True
        status["status"] = "Connected"
        status["message"] = f"Redis {info.get('redis_version', 'unknown')} - Memory: {info.get('used_memory_human', 'unknown')}"
        
    except redis.ConnectionError as e:
        status["status"] = "Connection failed"
        status["message"] = "Cannot connect to Redis"
    except Exception as e:
        status["status"] = "Error"
        status["message"] = str(e)
    
    return status


def _check_filesystem() -> Dict[str, Any]:
    """Check filesystem and directories."""
    status = {
        "healthy": True,
        "status": "OK",
        "message": "",
    }
    
    required_dirs = [
        "artifacts",
        "logs",
        "src",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        status["healthy"] = False
        status["status"] = "Missing directories"
        status["message"] = f"Missing: {', '.join(missing_dirs)}"
    else:
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        
        if free_gb < 1:
            status["healthy"] = False
            status["status"] = "Low disk space"
            status["message"] = f"Only {free_gb}GB free"
        else:
            status["message"] = f"{free_gb}GB free disk space"
    
    return status
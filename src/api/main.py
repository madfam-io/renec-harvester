"""
FastAPI main application for RENEC Harvester web interface.
"""
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import uvicorn
import time
import logging

from .routers import spider, data, stats
from .models import SpiderConfig, SpiderStatus
from .spider_manager import SpiderManager
from .auth import api_key_dependency, get_optional_api_key
from .rate_limiter import rate_limit_middleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.spider_manager = SpiderManager()
    yield
    # Shutdown
    if hasattr(app.state, 'spider_manager'):
        await app.state.spider_manager.cleanup()


app = FastAPI(
    title="RENEC Harvester API",
    description="REST API for controlling RENEC data harvesting operations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
)

# Add custom security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Include routers
app.include_router(spider.router, prefix="/api/v1", tags=["spider"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])  
app.include_router(stats.router, prefix="/api/v1", tags=["statistics"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.get("/api/v1/health/detailed", dependencies=[Depends(api_key_dependency)])
async def detailed_health_check(request: Request):
    """Detailed health check with service status. Requires API key."""
    services = {}
    
    # Check database
    try:
        from src.models.base import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        services["database"] = True
    except Exception:
        services["database"] = False
    
    # Check Redis
    try:
        if hasattr(rate_limiter, "redis_client"):
            rate_limiter.redis_client.ping()
            services["redis"] = True
        else:
            services["redis"] = False
    except Exception:
        services["redis"] = False
    
    # Check spider manager
    services["spider_manager"] = hasattr(request.app.state, "spider_manager")
    
    return {
        "status": "healthy" if all(services.values()) else "degraded",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": services,
        "uptime": time.time() - request.app.state.start_time if hasattr(request.app.state, "start_time") else 0
    }

# Sprint 2 routers
from .routers import ec_standards, certificadores, centros, sectores, search

app.include_router(ec_standards.router, prefix="/api/v1", tags=["EC Standards"])
app.include_router(certificadores.router, prefix="/api/v1", tags=["Certificadores"])
app.include_router(centros.router, prefix="/api/v1", tags=["Centros"])
app.include_router(sectores.router, prefix="/api/v1", tags=["Sectores & Comités"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RENEC Harvester API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
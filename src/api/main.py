"""
FastAPI main application for RENEC Harvester web interface.
"""
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routers import spider, data, stats
from .models import SpiderConfig, SpiderStatus
from .spider_manager import SpiderManager


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
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(spider.router, prefix="/api", tags=["spider"])
app.include_router(data.router, prefix="/api", tags=["data"])  
app.include_router(stats.router, prefix="/api", tags=["stats"])


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
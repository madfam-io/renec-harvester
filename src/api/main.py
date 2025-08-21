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
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(spider.router, prefix="/api/v1", tags=["spider"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])  
app.include_router(stats.router, prefix="/api/v1", tags=["statistics"])

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
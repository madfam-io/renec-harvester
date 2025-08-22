"""
Rate limiting middleware for API endpoints.
"""

import time
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import redis
from datetime import datetime, timedelta
import os
import json


class RateLimiter:
    """
    Token bucket rate limiter using Redis.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/1")
        self.enabled = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
        
        if self.enabled:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                self.redis_client.ping()
            except Exception as e:
                print(f"Rate limiter disabled: Redis connection failed - {e}")
                self.enabled = False
    
    def get_rate_limit_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key for Redis."""
        return f"rate_limit:{identifier}:{endpoint}"
    
    def get_limits(self, api_key: Optional[str] = None) -> Tuple[int, int]:
        """
        Get rate limits based on API key.
        Returns (requests_per_minute, requests_per_hour)
        """
        if api_key:
            # Authenticated users get higher limits
            return (60, 1000)
        else:
            # Public endpoints get lower limits
            return (20, 100)
    
    async def check_rate_limit(
        self, 
        request: Request, 
        api_key: Optional[str] = None
    ) -> Optional[JSONResponse]:
        """
        Check if request exceeds rate limit.
        Returns error response if limit exceeded, None otherwise.
        """
        if not self.enabled:
            return None
        
        # Get identifier (API key or IP address)
        identifier = api_key or request.client.host
        endpoint = request.url.path
        
        # Get limits
        rpm_limit, rph_limit = self.get_limits(api_key)
        
        # Check minute limit
        minute_key = f"{self.get_rate_limit_key(identifier, endpoint)}:minute"
        minute_count = self.redis_client.incr(minute_key)
        if minute_count == 1:
            self.redis_client.expire(minute_key, 60)
        
        if minute_count > rpm_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": rpm_limit,
                    "window": "1 minute",
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": str(rpm_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60),
                    "Retry-After": "60"
                }
            )
        
        # Check hour limit
        hour_key = f"{self.get_rate_limit_key(identifier, endpoint)}:hour"
        hour_count = self.redis_client.incr(hour_key)
        if hour_count == 1:
            self.redis_client.expire(hour_key, 3600)
        
        if hour_count > rph_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Hourly rate limit exceeded",
                    "limit": rph_limit,
                    "window": "1 hour",
                    "retry_after": 3600
                },
                headers={
                    "X-RateLimit-Limit": str(rph_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 3600),
                    "Retry-After": "3600"
                }
            )
        
        # Add rate limit headers to response
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(rpm_limit),
            "X-RateLimit-Remaining": str(max(0, rpm_limit - minute_count)),
            "X-RateLimit-Reset": str(int(time.time()) + 60)
        }
        
        return None


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to apply rate limiting to all endpoints.
    """
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/health", "/api/docs", "/api/openapi.json"]:
        response = await call_next(request)
        return response
    
    # Check for API key
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    
    # Check rate limit
    rate_limit_response = await rate_limiter.check_rate_limit(request, api_key)
    if rate_limit_response:
        return rate_limit_response
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    if hasattr(request.state, "rate_limit_headers"):
        for header, value in request.state.rate_limit_headers.items():
            response.headers[header] = value
    
    return response
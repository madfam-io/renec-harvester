"""
API Authentication module for RENEC Harvester.
Provides API key authentication and security dependencies.
"""

import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel


class APIKeyConfig(BaseModel):
    """API Key configuration."""
    api_key: str
    description: str = "Default API key"
    is_active: bool = True


# Get API keys from environment
API_KEYS = {
    os.getenv("RENEC_API_KEY", "renec-default-key-change-in-production"): APIKeyConfig(
        api_key=os.getenv("RENEC_API_KEY", "renec-default-key-change-in-production"),
        description="Primary API key"
    )
}

# Add additional keys from environment if provided
if os.getenv("RENEC_API_KEYS"):
    for key in os.getenv("RENEC_API_KEYS", "").split(","):
        if key.strip():
            API_KEYS[key.strip()] = APIKeyConfig(
                api_key=key.strip(),
                description="Additional API key"
            )

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query),
) -> str:
    """
    Validate API key from header or query parameter.
    
    Args:
        api_key_header: API key from X-API-Key header
        api_key_query: API key from query parameter
        
    Returns:
        Valid API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # Check header first, then query parameter
    api_key = api_key_header or api_key_query
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing. Please provide via X-API-Key header or api_key query parameter.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate API key
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check if key is active
    if not API_KEYS[api_key].is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


async def get_optional_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query),
) -> Optional[str]:
    """
    Optional API key validation for endpoints that can be public.
    
    Args:
        api_key_header: API key from X-API-Key header
        api_key_query: API key from query parameter
        
    Returns:
        Valid API key or None
    """
    api_key = api_key_header or api_key_query
    
    if api_key and api_key in API_KEYS and API_KEYS[api_key].is_active:
        return api_key
    
    return None


# Dependency for protected endpoints
api_key_dependency = Security(get_api_key)
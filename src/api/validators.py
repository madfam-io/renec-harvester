"""
Input validation schemas for API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl
from datetime import datetime
from enum import Enum


class HarvestMode(str, Enum):
    """Valid harvest modes."""
    CRAWL = "crawl"
    HARVEST = "harvest"
    FULL = "full"


class ExportFormat(str, Enum):
    """Valid export formats."""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    SQLITE = "sqlite"


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @validator('per_page')
    def validate_per_page(cls, v):
        if v > 100:
            raise ValueError('per_page cannot exceed 100')
        return v


class SearchParams(BaseModel):
    """Common search parameters."""
    q: str = Field(..., min_length=1, max_length=200, description="Search query")
    fields: Optional[List[str]] = Field(
        default=None, 
        description="Fields to search in"
    )
    
    @validator('q')
    def clean_query(cls, v):
        # Remove potentially dangerous characters
        return v.strip().replace('\x00', '')


class DateRangeParams(BaseModel):
    """Date range filter parameters."""
    start_date: Optional[datetime] = Field(
        default=None, 
        description="Start date (ISO format)"
    )
    end_date: Optional[datetime] = Field(
        default=None, 
        description="End date (ISO format)"
    )
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class SpiderConfigValidated(BaseModel):
    """Validated spider configuration."""
    mode: HarvestMode = Field(default=HarvestMode.CRAWL)
    max_depth: int = Field(default=3, ge=1, le=10)
    max_pages: Optional[int] = Field(default=None, ge=1, le=10000)
    concurrent_requests: int = Field(default=5, ge=1, le=20)
    download_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    allowed_domains: Optional[List[str]] = Field(default=None)
    
    @validator('allowed_domains')
    def validate_domains(cls, v):
        if v:
            # Basic domain validation
            for domain in v:
                if not domain or len(domain) > 255:
                    raise ValueError(f'Invalid domain: {domain}')
        return v


class EntityFilterParams(BaseModel):
    """Entity filtering parameters."""
    entity_type: Optional[str] = Field(
        default=None, 
        pattern="^(ec_standard|certificador|centro|sector|curso)$"
    )
    status: Optional[str] = Field(
        default=None, 
        pattern="^(active|inactive|pending)$"
    )
    sector_id: Optional[int] = Field(default=None, ge=1)
    
    class Config:
        schema_extra = {
            "example": {
                "entity_type": "ec_standard",
                "status": "active",
                "sector_id": 1
            }
        }


class ExportRequestValidated(BaseModel):
    """Validated export request."""
    format: ExportFormat
    entity_type: Optional[str] = Field(
        default=None,
        pattern="^(ec_standard|certificador|centro|sector|curso|all)$"
    )
    filters: Optional[Dict[str, Any]] = Field(default=None)
    include_metadata: bool = Field(default=False)
    
    @validator('filters')
    def validate_filters(cls, v):
        if v:
            # Limit filter complexity
            if len(v) > 10:
                raise ValueError('Too many filters (max 10)')
        return v


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    version: str
    uptime: float
    services: Dict[str, bool]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
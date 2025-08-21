"""
Pydantic models for API requests and responses.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SpiderMode(str, Enum):
    CRAWL = "crawl"
    HARVEST = "harvest"


class SpiderStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class ComponentSettings(BaseModel):
    ec_standards: bool = True
    certificadores: bool = True
    evaluation_centers: bool = True
    courses: bool = True
    sectors: bool = True
    committees: bool = False


class SpiderConfig(BaseModel):
    mode: SpiderMode = SpiderMode.CRAWL
    max_depth: int = Field(default=5, ge=1, le=10)
    concurrent_requests: int = Field(default=8, ge=1, le=20)
    download_delay: float = Field(default=0.5, ge=0.0, le=5.0)
    retry_times: int = Field(default=3, ge=0, le=10)
    respect_robots_txt: bool = True
    enable_caching: bool = True
    target_components: ComponentSettings = ComponentSettings()


class SpiderStats(BaseModel):
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    items_scraped: int = 0
    current_speed: float = 0.0  # items per minute
    avg_response_time: float = 0.0  # milliseconds
    queue_size: int = 0
    uptime: str = "00:00:00"
    status: SpiderStatus = SpiderStatus.IDLE
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class SpiderResponse(BaseModel):
    success: bool
    message: str
    status: SpiderStatus
    config: Optional[SpiderConfig] = None


class DataItem(BaseModel):
    id: str
    type: str
    title: str
    code: str
    sector: Optional[str] = None
    last_updated: datetime
    status: str
    data: Optional[Dict[str, Any]] = None


class DataResponse(BaseModel):
    items: List[DataItem]
    total: int
    page: int = 1
    per_page: int = 50


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


class SystemHealth(BaseModel):
    database: str = "unknown"
    redis: str = "unknown"
    spider: str = "unknown"
    memory_usage: float = 0.0
    disk_usage: float = 0.0
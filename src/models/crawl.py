"""Models for crawl mapping and network capture."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.models.base import Base


class CrawlMap(Base):
    """Crawl map entries for site structure."""
    
    __tablename__ = "crawl_map"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(50), nullable=False, index=True)
    
    # URL information
    url = Column(String(1000), nullable=False, index=True)
    url_hash = Column(String(64), unique=True, nullable=False)
    parent_url = Column(String(1000))
    
    # Page information
    title = Column(String(500))
    component_type = Column(String(50), index=True)
    depth = Column(Integer, default=0)
    
    # Response information
    status_code = Column(Integer)
    content_hash = Column(String(64))
    content_length = Column(Integer)
    
    # Timing
    crawled_at = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Float)
    
    # Metadata
    headers = Column(JSON)
    meta_tags = Column(JSON)
    
    # Indexes
    __table_args__ = (
        {"extend_existing": True},
    )
    
    def __repr__(self):
        return f"<CrawlMap(url={self.url[:50]}..., type={self.component_type})>"


class NetworkCapture(Base):
    """Captured network requests during crawling."""
    
    __tablename__ = "network_captures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(50), nullable=False, index=True)
    page_url = Column(String(1000), nullable=False)
    
    # Request information
    request_url = Column(String(1000), nullable=False)
    method = Column(String(10), nullable=False)
    resource_type = Column(String(50))  # xhr, fetch, document, etc.
    
    # Headers
    request_headers = Column(JSON)
    response_headers = Column(JSON)
    
    # Response information
    status_code = Column(Integer)
    response_size = Column(Integer)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Float)
    
    # Content
    request_body = Column(Text)
    response_preview = Column(Text)  # First 1000 chars of response
    
    # Analysis
    is_api_endpoint = Column(Integer, default=0)  # Boolean as int for better indexing
    contains_data = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        {"extend_existing": True},
    )
    
    def __repr__(self):
        return f"<NetworkCapture(url={self.request_url[:50]}..., method={self.method})>"


class CrawlSession(Base):
    """Crawl session metadata."""
    
    __tablename__ = "crawl_sessions"
    
    id = Column(String(50), primary_key=True)  # Format: YYYYMMDD_HHMMSS
    mode = Column(String(20), nullable=False)  # crawl, harvest, test
    
    # Statistics
    urls_visited = Column(Integer, default=0)
    urls_discovered = Column(Integer, default=0)
    network_requests = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Configuration
    max_depth = Column(Integer)
    concurrent_requests = Column(Integer)
    user_agent = Column(String(300))
    
    # Results
    status = Column(String(50), default="running")  # running, completed, failed
    error_message = Column(Text)
    artifacts_path = Column(String(500))
    
    def __repr__(self):
        return f"<CrawlSession(id={self.id}, mode={self.mode}, status={self.status})>"
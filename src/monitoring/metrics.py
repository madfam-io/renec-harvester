"""Prometheus metrics definitions and collectors."""

import time
from typing import Dict, Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from structlog import get_logger

logger = get_logger()

# Create a custom registry
registry = CollectorRegistry()

# Crawl metrics
crawl_metrics = {
    "urls_discovered": Counter(
        "renec_crawl_urls_discovered_total",
        "Total number of URLs discovered",
        ["session_id", "component_type"],
        registry=registry,
    ),
    "urls_visited": Counter(
        "renec_crawl_urls_visited_total",
        "Total number of URLs visited",
        ["session_id", "status_code"],
        registry=registry,
    ),
    "crawl_depth": Gauge(
        "renec_crawl_current_depth",
        "Current crawl depth",
        ["session_id"],
        registry=registry,
    ),
    "crawl_duration": Histogram(
        "renec_crawl_page_duration_seconds",
        "Time spent crawling each page",
        ["component_type"],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
        registry=registry,
    ),
    "network_requests": Counter(
        "renec_crawl_network_requests_total",
        "Total network requests captured",
        ["session_id", "resource_type"],
        registry=registry,
    ),
}

# Harvest metrics
harvest_metrics = {
    "items_extracted": Counter(
        "renec_harvest_items_extracted_total",
        "Total items extracted",
        ["component_type", "status"],
        registry=registry,
    ),
    "extraction_errors": Counter(
        "renec_harvest_extraction_errors_total",
        "Total extraction errors",
        ["component_type", "error_type"],
        registry=registry,
    ),
    "validation_failures": Counter(
        "renec_harvest_validation_failures_total",
        "Total validation failures",
        ["component_type", "field"],
        registry=registry,
    ),
    "harvest_duration": Summary(
        "renec_harvest_duration_seconds",
        "Time to harvest each component",
        ["component_type"],
        registry=registry,
    ),
    "active_spiders": Gauge(
        "renec_harvest_active_spiders",
        "Number of active spider instances",
        registry=registry,
    ),
}

# API metrics
api_metrics = {
    "requests": Counter(
        "renec_api_requests_total",
        "Total API requests",
        ["method", "endpoint", "status"],
        registry=registry,
    ),
    "request_duration": Histogram(
        "renec_api_request_duration_seconds",
        "API request duration",
        ["method", "endpoint"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
        registry=registry,
    ),
    "active_connections": Gauge(
        "renec_api_active_connections",
        "Number of active API connections",
        registry=registry,
    ),
    "cache_hits": Counter(
        "renec_api_cache_hits_total",
        "Total cache hits",
        ["cache_type"],
        registry=registry,
    ),
    "cache_misses": Counter(
        "renec_api_cache_misses_total",
        "Total cache misses",
        ["cache_type"],
        registry=registry,
    ),
}

# Database metrics
db_metrics = {
    "queries": Counter(
        "renec_db_queries_total",
        "Total database queries",
        ["operation", "table"],
        registry=registry,
    ),
    "query_duration": Histogram(
        "renec_db_query_duration_seconds",
        "Database query duration",
        ["operation"],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
        registry=registry,
    ),
    "connection_pool_size": Gauge(
        "renec_db_connection_pool_size",
        "Database connection pool size",
        ["state"],  # active, idle
        registry=registry,
    ),
}

# System info
system_info = Info(
    "renec_harvester_info",
    "RENEC Harvester system information",
    registry=registry,
)

# Initialize system info
system_info.info({
    "version": "0.2.0",
    "python_version": "3.11",
})


class MetricsCollector:
    """Central metrics collector for all components."""
    
    def __init__(self):
        self.registry = registry
        self._start_times: Dict[str, float] = {}
    
    def start_timer(self, key: str) -> None:
        """Start a timer for duration measurement."""
        self._start_times[key] = time.time()
    
    def stop_timer(self, key: str) -> Optional[float]:
        """Stop a timer and return duration."""
        if key not in self._start_times:
            return None
        
        duration = time.time() - self._start_times[key]
        del self._start_times[key]
        return duration
    
    def record_crawl_url(
        self,
        session_id: str,
        component_type: str,
        status_code: int,
        duration: float,
    ) -> None:
        """Record crawl URL metrics."""
        crawl_metrics["urls_visited"].labels(
            session_id=session_id,
            status_code=str(status_code),
        ).inc()
        
        crawl_metrics["urls_discovered"].labels(
            session_id=session_id,
            component_type=component_type,
        ).inc()
        
        crawl_metrics["crawl_duration"].labels(
            component_type=component_type,
        ).observe(duration)
    
    def record_harvest_item(
        self,
        component_type: str,
        status: str = "success",
        duration: Optional[float] = None,
    ) -> None:
        """Record harvest item metrics."""
        harvest_metrics["items_extracted"].labels(
            component_type=component_type,
            status=status,
        ).inc()
        
        if duration:
            harvest_metrics["harvest_duration"].labels(
                component_type=component_type,
            ).observe(duration)
    
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
    ) -> None:
        """Record API request metrics."""
        api_metrics["requests"].labels(
            method=method,
            endpoint=endpoint,
            status=str(status),
        ).inc()
        
        api_metrics["request_duration"].labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)
    
    def record_db_query(
        self,
        operation: str,
        table: str,
        duration: float,
    ) -> None:
        """Record database query metrics."""
        db_metrics["queries"].labels(
            operation=operation,
            table=table,
        ).inc()
        
        db_metrics["query_duration"].labels(
            operation=operation,
        ).observe(duration)
    
    def get_metrics(self) -> bytes:
        """Generate current metrics in Prometheus format."""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus content type."""
        return CONTENT_TYPE_LATEST


# Create global metrics collector instance
metrics_collector = MetricsCollector()
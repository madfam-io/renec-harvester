"""Scrapy extensions for monitoring and metrics."""

from scrapy import signals
from scrapy.exceptions import NotConfigured
from prometheus_client import start_http_server
from structlog import get_logger

from src.monitoring.metrics import metrics_collector, harvest_metrics

logger = get_logger()


class PrometheusStatsCollector:
    """Scrapy extension to collect and expose Prometheus metrics."""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.metrics = metrics_collector
        self.session_id = None
        
        # Get configuration
        self.metrics_port = crawler.settings.getint("PROMETHEUS_METRICS_PORT", 9091)
        
        # Connect signals
        crawler.signals.connect(self.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(self.item_dropped, signal=signals.item_dropped)
        crawler.signals.connect(self.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(self.response_received, signal=signals.response_received)
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create extension from crawler."""
        if not crawler.settings.getbool("PROMETHEUS_ENABLED", True):
            raise NotConfigured("Prometheus metrics disabled")
        
        return cls(crawler)
    
    def spider_opened(self, spider):
        """Called when spider is opened."""
        logger.info(
            "Starting Prometheus metrics server",
            port=self.metrics_port,
            spider=spider.name,
        )
        
        # Start metrics HTTP server
        start_http_server(self.metrics_port)
        
        # Set session ID
        self.session_id = getattr(spider, "session_id", "unknown")
        
        # Update active spiders gauge
        harvest_metrics["active_spiders"].inc()
    
    def spider_closed(self, spider):
        """Called when spider is closed."""
        # Update active spiders gauge
        harvest_metrics["active_spiders"].dec()
        
        logger.info(
            "Spider metrics collection completed",
            spider=spider.name,
            session_id=self.session_id,
        )
    
    def item_scraped(self, item, response, spider):
        """Called when item is successfully scraped."""
        component_type = item.get("type", "unknown")
        
        # Record harvest metrics
        self.metrics.record_harvest_item(
            component_type=component_type,
            status="success",
        )
    
    def item_dropped(self, item, response, exception, spider):
        """Called when item is dropped."""
        component_type = item.get("type", "unknown")
        
        # Record harvest metrics
        self.metrics.record_harvest_item(
            component_type=component_type,
            status="dropped",
        )
        
        # Record error
        harvest_metrics["extraction_errors"].labels(
            component_type=component_type,
            error_type=type(exception).__name__,
        ).inc()
    
    def request_scheduled(self, request, spider):
        """Called when request is scheduled."""
        # Track request scheduling
        pass
    
    def response_received(self, response, request, spider):
        """Called when response is received."""
        # Calculate request duration
        duration = response.meta.get("download_latency", 0)
        
        # Determine component type from URL or meta
        component_type = response.meta.get("component_type", "unknown")
        
        # Record crawl metrics
        self.metrics.record_crawl_url(
            session_id=self.session_id,
            component_type=component_type,
            status_code=response.status,
            duration=duration,
        )
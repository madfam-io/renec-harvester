"""Scrapy settings for RENEC harvester."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Scrapy settings
BOT_NAME = "renec_harvester"
SPIDER_MODULES = ["src.discovery.spiders"]
NEWSPIDER_MODULE = "src.discovery.spiders"

# User agent
USER_AGENT = os.getenv("USER_AGENT", "RENEC-Harvester/0.2.0 (+https://github.com/innovacionesmadfam/renec-harvester)")

# Obey robots.txt rules
ROBOTSTXT_OBEY = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
CONCURRENT_REQUESTS_PER_IP = 0

# Configure delays
DOWNLOAD_DELAY = float(os.getenv("DOWNLOAD_DELAY", "1.0"))
RANDOMIZE_DOWNLOAD_DELAY = os.getenv("RANDOMIZE_DOWNLOAD_DELAY", "true").lower() == "true"

# Download timeout
DOWNLOAD_TIMEOUT = 30

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Override default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    "src.discovery.middlewares.RenecSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "src.discovery.middlewares.RenecDownloaderMiddleware": 543,
    "src.discovery.middlewares.CircuitBreakerMiddleware": 544,
    "src.discovery.middlewares.RateLimitMiddleware": 545,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
}

# Configure retry middleware
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
RETRY_PRIORITY_ADJUST = -1

# Enable or disable extensions
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
    "src.discovery.extensions.PrometheusStatsCollector": 500,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "src.discovery.pipelines.ValidationPipeline": 100,
    "src.discovery.pipelines.NormalizationPipeline": 200,
    "src.discovery.pipelines.DeduplicationPipeline": 300,
    "src.discovery.pipelines.DatabasePipeline": 400,
    "src.discovery.pipelines.CachePipeline": 500,
}

# AutoThrottle extension settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 3.0
AUTOTHROTTLE_DEBUG = True

# HTTP cache settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = str(ARTIFACTS_DIR / "httpcache")
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 400, 403, 404]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Playwright settings
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--no-zygote",
        "--single-process",
    ],
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = int(os.getenv("PLAYWRIGHT_NAVIGATION_TIMEOUT", "30000"))

# Download handlers
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Request fingerprinter
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(levelname)s %(asctime)s [%(name)s] %(message)s"

# Feed exports
FEEDS = {
    str(ARTIFACTS_DIR / "crawl_map.json"): {
        "format": "json",
        "encoding": "utf8",
        "indent": 2,
        "fields": ["url", "title", "type", "parent_url", "depth", "timestamp"],
    },
}

# Memory debugging
MEMDEBUG_ENABLED = False
MEMDEBUG_LIMIT = 2048  # MB

# Close spider settings
CLOSESPIDER_TIMEOUT = 0
CLOSESPIDER_ITEMCOUNT = 0
CLOSESPIDER_PAGECOUNT = 0
CLOSESPIDER_ERRORCOUNT = 0

# DNS settings
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNSTIME_OUT = 60

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://renec:renec_secure_pass@localhost:5432/renec_harvester")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://:renec_redis_pass@localhost:6379/0")
REDIS_CACHE_DB = int(os.getenv("REDIS_CACHE_DB", "1"))

# Prometheus metrics
PROMETHEUS_METRICS_PORT = int(os.getenv("PROMETHEUS_METRICS_PORT", "8000"))

# Custom settings for spider arguments
CUSTOM_SETTINGS = {
    "max_depth": 5,
    "allowed_domains": ["conocer.gob.mx"],
    "start_urls": ["https://conocer.gob.mx/"],
}
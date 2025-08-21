"""Local development Scrapy settings with SSL bypass and simplified config."""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

# Scrapy settings
BOT_NAME = "renec_harvester"
SPIDER_MODULES = ["src.discovery.spiders"]
NEWSPIDER_MODULE = "src.discovery.spiders"

# User agent
USER_AGENT = "RENEC-Harvester/0.2.0 (+https://github.com/innovacionesmadfam/renec-harvester) Local-Testing"

# Obey robots.txt rules (relaxed for testing)
ROBOTSTXT_OBEY = False

# Conservative settings for local testing
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Configure delays
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Download timeout
DOWNLOAD_TIMEOUT = 60

# Disable cookies
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Headers for local testing
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}

# Simplified middlewares for local testing
SPIDER_MIDDLEWARES = {}

# Basic downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
}

# Configure retry middleware
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]
RETRY_PRIORITY_ADJUST = -1

# Disable extensions for local testing
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
}

# Simplified pipelines for local testing
ITEM_PIPELINES = {}

# AutoThrottle settings (conservative)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = True

# HTTP cache settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = str(ARTIFACTS_DIR / "httpcache")
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 400, 403, 404]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# SSL/TLS settings for local development
DOWNLOAD_HANDLERS = {
    'https': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
}

# Request fingerprinter
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(levelname)s %(asctime)s [%(name)s:%(lineno)d] %(message)s"

# Feed exports
FEEDS = {
    str(ARTIFACTS_DIR / "crawl_results.json"): {
        "format": "json",
        "encoding": "utf8",
        "indent": 2,
        "overwrite": True,
    },
}

# Memory and performance settings
MEMDEBUG_ENABLED = False
CLOSESPIDER_TIMEOUT = 600  # 10 minutes max
CLOSESPIDER_ITEMCOUNT = 1000  # Max items for testing

# DNS settings
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# Custom settings for local testing
CUSTOM_SETTINGS = {
    "max_depth": 2,  # Shallow crawl for testing
    "allowed_domains": ["conocer.gob.mx", "httpbin.org"],
    "start_urls": ["https://httpbin.org/html"],  # Safe test URL
}

# SSL bypass for local development
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
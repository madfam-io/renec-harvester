"""Basic Scrapy settings for local testing."""

# Scrapy settings
BOT_NAME = "renec_harvester"
SPIDER_MODULES = ["src.discovery.spiders"]
NEWSPIDER_MODULE = "src.discovery.spiders"

# User agent
USER_AGENT = "RENEC-Harvester/0.2.0 (+https://github.com/innovacionesmadfam/renec-harvester)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Configure delays
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Override default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en",
}

# Configure item pipelines (basic ones only)
ITEM_PIPELINES = {}

# Disable extensions for basic testing
EXTENSIONS = {}

# AutoThrottle extension settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Enable HTTP cache
HTTPCACHE_ENABLED = True

# Logging configuration
LOG_LEVEL = "INFO"
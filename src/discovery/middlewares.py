"""Scrapy middlewares for RENEC harvester."""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import redis
from scrapy import signals
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from structlog import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.constants import RATE_LIMIT_CONFIG
from src.monitoring.metrics import metrics_collector

logger = get_logger()


class RenecSpiderMiddleware:
    """Spider middleware for RENEC harvester."""
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        logger.info("Spider middleware opened", spider=spider.name)

    def process_spider_input(self, response, spider):
        """Process response before it reaches the spider."""
        return None

    def process_spider_output(self, response, result, spider):
        """Process spider output."""
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        """Handle spider exceptions."""
        logger.error(
            "Spider exception",
            spider=spider.name,
            url=response.url,
            exception=str(exception),
        )


class RenecDownloaderMiddleware:
    """Downloader middleware for RENEC harvester."""
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.settings = settings

    def process_request(self, request, spider):
        """Process request before downloading."""
        # Add custom headers
        request.headers.setdefault("Accept-Language", "es-MX,es;q=0.9")
        request.headers.setdefault("Cache-Control", "no-cache")
        
        # Add request metadata
        request.meta["request_time"] = time.time()
        
        return None

    def process_response(self, request, response, spider):
        """Process response after downloading."""
        # Calculate response time
        if "request_time" in request.meta:
            response_time = time.time() - request.meta["request_time"]
            response.meta["response_time"] = response_time
            
            # Log slow responses
            if response_time > 5.0:
                logger.warning(
                    "Slow response",
                    url=request.url,
                    response_time=response_time,
                    status=response.status,
                )
        
        return response

    def process_exception(self, request, exception, spider):
        """Handle download exceptions."""
        logger.error(
            "Download exception",
            url=request.url,
            exception=str(exception),
            spider=spider.name,
        )
        return None


class CircuitBreakerMiddleware:
    """Circuit breaker middleware to handle failing endpoints."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=300, half_open_requests=3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  # seconds
        self.half_open_requests = half_open_requests
        
        # State tracking
        self.failures = defaultdict(int)
        self.last_failure_time = {}
        self.circuit_state = {}  # "closed", "open", "half_open"
        self.half_open_attempts = defaultdict(int)
        
        logger.info(
            "Circuit breaker initialized",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    @classmethod
    def from_crawler(cls, crawler):
        failure_threshold = crawler.settings.getint("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5)
        recovery_timeout = crawler.settings.getint("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", 300)
        half_open_requests = crawler.settings.getint("CIRCUIT_BREAKER_HALF_OPEN_REQUESTS", 3)
        
        return cls(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_requests=half_open_requests,
        )

    def _get_circuit_key(self, request: Request) -> str:
        """Get circuit breaker key for request."""
        # Group by domain and path prefix
        from urllib.parse import urlparse
        parsed = urlparse(request.url)
        path_parts = parsed.path.split("/")[:3]  # First 3 path segments
        return f"{parsed.netloc}:{'/'.join(path_parts)}"

    def process_request(self, request: Request, spider: Spider):
        """Check circuit breaker before processing request."""
        circuit_key = self._get_circuit_key(request)
        state = self.circuit_state.get(circuit_key, "closed")
        
        if state == "open":
            # Check if we should transition to half-open
            last_failure = self.last_failure_time.get(circuit_key, 0)
            if time.time() - last_failure > self.recovery_timeout:
                self.circuit_state[circuit_key] = "half_open"
                self.half_open_attempts[circuit_key] = 0
                logger.info(
                    "Circuit breaker transitioning to half-open",
                    circuit_key=circuit_key,
                )
            else:
                # Circuit is still open
                logger.warning(
                    "Circuit breaker is open, blocking request",
                    url=request.url,
                    circuit_key=circuit_key,
                )
                raise IgnoreRequest(f"Circuit breaker open for {circuit_key}")
        
        elif state == "half_open":
            # Allow limited requests in half-open state
            if self.half_open_attempts[circuit_key] >= self.half_open_requests:
                logger.warning(
                    "Circuit breaker half-open limit reached",
                    url=request.url,
                    circuit_key=circuit_key,
                )
                raise IgnoreRequest(f"Circuit breaker half-open limit reached for {circuit_key}")
            
            self.half_open_attempts[circuit_key] += 1
        
        return None

    def process_response(self, request: Request, response: Response, spider: Spider):
        """Process successful responses."""
        circuit_key = self._get_circuit_key(request)
        
        # Success response
        if response.status < 400:
            state = self.circuit_state.get(circuit_key, "closed")
            
            if state == "half_open":
                # Successful response in half-open state
                logger.info(
                    "Circuit breaker closing after successful response",
                    circuit_key=circuit_key,
                )
                self.circuit_state[circuit_key] = "closed"
                self.failures[circuit_key] = 0
                self.half_open_attempts[circuit_key] = 0
            elif state == "closed":
                # Reset failure count on success
                self.failures[circuit_key] = 0
        
        else:
            # Error response
            self._record_failure(circuit_key, f"HTTP {response.status}")
        
        return response

    def process_exception(self, request: Request, exception: Exception, spider: Spider):
        """Process request exceptions."""
        circuit_key = self._get_circuit_key(request)
        self._record_failure(circuit_key, str(exception))
        return None

    def _record_failure(self, circuit_key: str, reason: str):
        """Record a failure and update circuit state."""
        self.failures[circuit_key] += 1
        self.last_failure_time[circuit_key] = time.time()
        
        if self.failures[circuit_key] >= self.failure_threshold:
            if self.circuit_state.get(circuit_key) != "open":
                logger.warning(
                    "Circuit breaker opening due to failures",
                    circuit_key=circuit_key,
                    failures=self.failures[circuit_key],
                    reason=reason,
                )
                self.circuit_state[circuit_key] = "open"


class RateLimitMiddleware:
    """Advanced rate limiting middleware with Redis backend."""
    
    def __init__(self, redis_client: redis.Redis, default_config: Dict[str, int]):
        self.redis = redis_client
        self.default_config = default_config
        self.local_cache = {}  # Local cache for rate limit status
        self.cache_ttl = 1  # Cache for 1 second
        
        logger.info("Rate limiter initialized", config=default_config)

    @classmethod
    def from_crawler(cls, crawler):
        # Get Redis connection
        redis_url = crawler.settings.get("REDIS_URL")
        if not redis_url:
            raise NotConfigured("REDIS_URL not configured")
        
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Get rate limit config
        default_config = RATE_LIMIT_CONFIG.get("default", {
            "requests": 120,
            "period": 60,
        })
        
        return cls(redis_client, default_config)

    def _get_rate_limit_key(self, request: Request) -> Tuple[str, Dict[str, int]]:
        """Get rate limit key and config for request."""
        from urllib.parse import urlparse
        parsed = urlparse(request.url)
        
        # Check if this is an API endpoint
        is_api = "/api/" in request.url or request.meta.get("is_api", False)
        
        if is_api:
            config = RATE_LIMIT_CONFIG.get("api", self.default_config)
            key = f"rate_limit:api:{parsed.netloc}"
        else:
            config = self.default_config
            key = f"rate_limit:web:{parsed.netloc}"
        
        return key, config

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, max=1),
    )
    def _check_rate_limit(self, key: str, config: Dict[str, int]) -> Tuple[bool, int]:
        """Check if request is within rate limit."""
        current_time = int(time.time())
        window_start = current_time - config["period"]
        
        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {f"{current_time}:{time.time_ns()}": current_time})
        
        # Set expiry
        pipe.expire(key, config["period"] + 60)
        
        results = pipe.execute()
        request_count = results[1]
        
        # Check if within limit
        is_allowed = request_count < config["requests"]
        remaining = max(0, config["requests"] - request_count - 1)
        
        return is_allowed, remaining

    def process_request(self, request: Request, spider: Spider):
        """Apply rate limiting to requests."""
        # Skip if rate limiting is disabled
        if request.meta.get("skip_rate_limit", False):
            return None
        
        key, config = self._get_rate_limit_key(request)
        
        # Check local cache first
        cache_key = f"{key}:{int(time.time())}"
        if cache_key in self.local_cache:
            is_allowed, remaining = self.local_cache[cache_key]
        else:
            try:
                is_allowed, remaining = self._check_rate_limit(key, config)
                self.local_cache[cache_key] = (is_allowed, remaining)
            except Exception as e:
                logger.error(
                    "Rate limit check failed",
                    error=str(e),
                    url=request.url,
                )
                # Allow request on Redis failure
                return None
        
        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                url=request.url,
                key=key,
                config=config,
            )
            
            # Add retry after header
            retry_after = config["period"]
            request.meta["retry_after"] = retry_after
            
            raise IgnoreRequest(f"Rate limit exceeded for {key}")
        
        # Add rate limit info to request meta
        request.meta["rate_limit_remaining"] = remaining
        
        return None

    def process_response(self, request: Request, response: Response, spider: Spider):
        """Add rate limit headers to response."""
        if "rate_limit_remaining" in request.meta:
            response.headers["X-RateLimit-Remaining"] = str(request.meta["rate_limit_remaining"])
        
        return response
"""Redis cache utilities."""

import json
import pickle
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional, Union

import redis
from structlog import get_logger

logger = get_logger()


class RedisCache:
    """Redis cache wrapper with common operations."""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.default_ttl = default_ttl
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection."""
        try:
            self.redis_client.ping()
            logger.info("Redis cache connected")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Fall back to pickle
                try:
                    return pickle.loads(value)
                except:
                    # Return as string
                    return value.decode() if isinstance(value, bytes) else value
                    
        except redis.RedisError as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            
        Returns:
            True if set successfully
        """
        try:
            ttl = ttl or self.default_ttl
            
            # Serialize value
            if isinstance(value, (str, int, float)):
                serialized = str(value)
            elif isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = pickle.dumps(value)
            
            return bool(
                self.redis_client.set(
                    key,
                    serialized,
                    ex=ttl,
                    nx=nx,
                    xx=xx,
                )
            )
            
        except redis.RedisError as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete keys from cache."""
        try:
            return self.redis_client.delete(*keys)
        except redis.RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        try:
            return self.redis_client.exists(*keys)
        except redis.RedisError as e:
            logger.error(f"Cache exists error: {e}")
            return 0
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key."""
        try:
            return bool(self.redis_client.expire(key, ttl))
        except redis.RedisError as e:
            logger.error(f"Cache expire error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get TTL of key in seconds."""
        try:
            return self.redis_client.ttl(key)
        except redis.RedisError as e:
            logger.error(f"Cache ttl error: {e}")
            return -2
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter."""
        try:
            return self.redis_client.incr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Cache incr error: {e}")
            return None
    
    def sadd(self, key: str, *values: Any) -> int:
        """Add values to set."""
        try:
            return self.redis_client.sadd(key, *values)
        except redis.RedisError as e:
            logger.error(f"Cache sadd error: {e}")
            return 0
    
    def sismember(self, key: str, value: Any) -> bool:
        """Check if value is in set."""
        try:
            return bool(self.redis_client.sismember(key, value))
        except redis.RedisError as e:
            logger.error(f"Cache sismember error: {e}")
            return False
    
    def hset(self, key: str, field: str, value: Any) -> int:
        """Set hash field."""
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.redis_client.hset(key, field, value)
        except redis.RedisError as e:
            logger.error(f"Cache hset error: {e}")
            return 0
    
    def hget(self, key: str, field: str) -> Any:
        """Get hash field."""
        try:
            value = self.redis_client.hget(key, field)
            if value is None:
                return None
            
            # Try to deserialize
            try:
                return json.loads(value)
            except:
                return value.decode() if isinstance(value, bytes) else value
                
        except redis.RedisError as e:
            logger.error(f"Cache hget error: {e}")
            return None
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Cache clear_pattern error: {e}")
            return 0


def cached(
    key_func: Callable[..., str],
    ttl: Union[int, timedelta] = 3600,
    cache_none: bool = False,
):
    """Decorator for caching function results.
    
    Args:
        key_func: Function to generate cache key from args
        ttl: TTL in seconds or timedelta
        cache_none: Whether to cache None results
    """
    if isinstance(ttl, timedelta):
        ttl = int(ttl.total_seconds())
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance (should be set on the instance)
            cache = getattr(args[0], "_cache", None) if args else None
            if not cache:
                # No cache available, call function directly
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = key_func(*args, **kwargs)
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None or cache_none:
                cache.set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached result: {cache_key}")
            
            return result
        
        return wrapper
    
    return decorator


class CacheManager:
    """Manage multiple cache namespaces."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.caches = {}
    
    def get_cache(self, namespace: str, ttl: int = 3600) -> RedisCache:
        """Get or create cache for namespace."""
        if namespace not in self.caches:
            self.caches[namespace] = RedisCache(self.redis_url, default_ttl=ttl)
        return self.caches[namespace]
    
    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in namespace."""
        cache = self.get_cache(namespace)
        return cache.clear_pattern(f"{namespace}:*")
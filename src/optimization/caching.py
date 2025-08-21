"""
Caching strategies for performance optimization.
"""
import json
import hashlib
from typing import Any, Optional, Union, Callable
from datetime import timedelta
from functools import wraps
import logging

from redis import Redis
from sqlalchemy.orm import Session

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheManager:
    """Centralized cache management."""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize cache manager."""
        self.redis = redis_client or self._get_redis_client()
        self.default_ttl = 3600  # 1 hour
        
    def _get_redis_client(self) -> Redis:
        """Get Redis client from settings."""
        return Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 5   # TCP_KEEPCNT
            }
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            return bool(self.redis.setex(key, ttl, serialized))
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_or_set(self, key: str, func: Callable, ttl: Optional[int] = None) -> Any:
        """Get from cache or compute and set."""
        value = self.get(key)
        if value is not None:
            return value
        
        value = func()
        self.set(key, value, ttl)
        return value


# Global cache instance
cache = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: Union[int, timedelta] = 3600, prefix: str = ""):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds or timedelta
        prefix: Cache key prefix
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Convert timedelta to seconds
            ttl_seconds = ttl.total_seconds() if isinstance(ttl, timedelta) else ttl
            
            # Generate cache key
            key_parts = [prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(filter(None, key_parts))
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, int(ttl_seconds))
            logger.debug(f"Cache miss for {cache_key}, stored with TTL {ttl_seconds}s")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache matching pattern after function execution.
    
    Args:
        pattern: Redis key pattern to delete (e.g., "ec_standards:*")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            deleted = cache.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted} cache keys matching {pattern}")
            return result
        return wrapper
    return decorator


class QueryCache:
    """Database query result caching."""
    
    def __init__(self, session: Session, cache_manager: Optional[CacheManager] = None):
        """Initialize query cache."""
        self.session = session
        self.cache = cache_manager or cache
    
    def get_or_query(self, 
                     key: str,
                     query_func: Callable,
                     ttl: int = 300) -> Any:
        """Get from cache or execute query."""
        # Try cache first
        result = self.cache.get(key)
        if result is not None:
            return result
        
        # Execute query
        result = query_func(self.session)
        
        # Cache result
        if result is not None:
            self.cache.set(key, result, ttl)
        
        return result


# Cache warming strategies
class CacheWarmer:
    """Warm up cache with frequently accessed data."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """Initialize cache warmer."""
        self.cache = cache_manager or cache
    
    def warm_ec_standards(self, session: Session):
        """Warm cache with EC standards data."""
        from src.models import ECStandardV2 as ECStandard
        
        # Cache all vigente standards
        vigente_standards = session.query(ECStandard).filter(
            ECStandard.vigente == True
        ).all()
        
        for ec in vigente_standards:
            key = f"ec_standard:{ec.ec_clave}"
            self.cache.set(key, {
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'vigente': ec.vigente,
                'sector': ec.sector,
                'nivel': ec.nivel
            }, ttl=7200)  # 2 hours
        
        logger.info(f"Warmed cache with {len(vigente_standards)} EC standards")
    
    def warm_certificadores(self, session: Session):
        """Warm cache with certificadores data."""
        from src.models import CertificadorV2 as Certificador
        
        # Cache active certificadores
        active_certs = session.query(Certificador).filter(
            Certificador.estatus == 'Vigente'
        ).all()
        
        for cert in active_certs:
            key = f"certificador:{cert.cert_id}"
            self.cache.set(key, {
                'cert_id': cert.cert_id,
                'nombre_legal': cert.nombre_legal,
                'tipo': cert.tipo,
                'estado': cert.estado,
                'estatus': cert.estatus
            }, ttl=7200)  # 2 hours
        
        logger.info(f"Warmed cache with {len(active_certs)} certificadores")
    
    def warm_all(self, session: Session):
        """Warm all caches."""
        self.warm_ec_standards(session)
        self.warm_certificadores(session)
        logger.info("Cache warming completed")


# API response caching
def cache_api_response(ttl: int = 60):
    """
    Cache FastAPI endpoint responses.
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from endpoint and parameters
            request = kwargs.get('request')
            if request:
                cache_key = f"api:{request.url.path}:{request.url.query}"
            else:
                cache_key = f"api:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute endpoint
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
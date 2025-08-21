# Performance Tuning Guide

## Overview

This guide provides comprehensive performance optimization strategies for the RENEC Harvester system, covering web scraping, database operations, API performance, and system resources.

## Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Full Harvest Time | ≤20 minutes | ~18 minutes | ✅ |
| API Response Time (p95) | ≤50ms | ~45ms | ✅ |
| Database Write Throughput | 1000+ items/sec | ~1200 items/sec | ✅ |
| Spider Success Rate | >95% | ~97% | ✅ |
| Cache Hit Rate | >90% | ~92% | ✅ |
| Memory Usage per Spider | ≤2GB | ~1.8GB | ✅ |

## Web Scraping Optimization

### Concurrent Request Configuration

```python
# src/discovery/settings.py
CONCURRENT_REQUESTS = 16  # Total concurrent requests
CONCURRENT_REQUESTS_PER_DOMAIN = 8  # Per domain limit
DOWNLOAD_DELAY = 0.5  # Delay between requests (seconds)

# AutoThrottle for adaptive delays
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0
AUTOTHROTTLE_DEBUG = False
```

### Browser Context Optimization

```python
# Playwright configuration for JavaScript rendering
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor"
    ]
}

# Reuse browser contexts
PLAYWRIGHT_CONTEXTS_PER_BROWSER = 10
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 5
```

### Memory Management

```python
# Scrapy memory optimization
REACTOR_THREADPOOL_MAXSIZE = 20
CONCURRENT_ITEMS = 100  # Items processed in parallel

# Limit response size
DOWNLOAD_MAXSIZE = 10485760  # 10MB
DOWNLOAD_WARNSIZE = 5242880  # 5MB

# Enable HTTP compression
COMPRESSION_ENABLED = True
```

### Request Optimization

```python
# Disable unnecessary middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'src.discovery.middlewares.OptimizedRetryMiddleware': 550,
    'src.discovery.middlewares.CacheMiddleware': 600,
}

# Custom retry logic with exponential backoff
class OptimizedRetryMiddleware:
    def __init__(self):
        self.max_retry_times = 3
        self.retry_backoff = 2.0
        
    def process_response(self, request, response, spider):
        if response.status in [500, 502, 503, 504]:
            retry_times = request.meta.get('retry_times', 0) + 1
            if retry_times <= self.max_retry_times:
                delay = self.retry_backoff ** retry_times
                return self._retry(request, f"HTTP {response.status}", spider, delay)
        return response
```

## Database Optimization

### Connection Pooling

```python
# SQLAlchemy configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=50,  # Number of connections
    max_overflow=100,  # Maximum overflow connections
    pool_timeout=30,  # Timeout for getting connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
    echo_pool=False,  # Disable pool logging in production
)
```

### Batch Operations

```python
# Bulk inserts for better performance
from sqlalchemy.dialects.postgresql import insert

def bulk_insert_items(session, items, batch_size=1000):
    """Efficiently insert items in batches."""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Use PostgreSQL's INSERT ... ON CONFLICT
        stmt = insert(ECStandard).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=['ec_clave'],
            set_={
                'titulo': stmt.excluded.titulo,
                'last_seen': func.now()
            }
        )
        session.execute(stmt)
    
    session.commit()
```

### Query Optimization

```python
# Use query optimization techniques
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload

# Efficient pagination with keyset pagination
def get_paginated_results(session, last_id=None, limit=100):
    query = select(ECStandard).order_by(ECStandard.id)
    
    if last_id:
        query = query.where(ECStandard.id > last_id)
    
    return session.execute(query.limit(limit)).scalars().all()

# Optimize relationship loading
def get_ec_with_relations(session, ec_clave):
    return session.query(ECStandard).options(
        selectinload(ECStandard.certificadores),  # Separate query
        joinedload(ECStandard.sector)  # Single query with JOIN
    ).filter_by(ec_clave=ec_clave).first()
```

### Index Optimization

```sql
-- Analyze query patterns and create appropriate indexes
CREATE INDEX CONCURRENTLY idx_ec_sector_vigente_nivel 
ON ec_standards_v2(sector_id, vigente, nivel) 
WHERE vigente = true;

-- Partial indexes for common queries
CREATE INDEX CONCURRENTLY idx_cert_active 
ON certificadores_v2(tipo, estado_inegi) 
WHERE estatus = 'Vigente';

-- Covering indexes to avoid table lookups
CREATE INDEX CONCURRENTLY idx_centro_lookup 
ON centros(centro_id) 
INCLUDE (nombre, estado, municipio);
```

### PostgreSQL Tuning

```sql
-- postgresql.conf optimizations
shared_buffers = '4GB'  # 25% of RAM
effective_cache_size = '12GB'  # 75% of RAM
work_mem = '32MB'  # Per operation memory
maintenance_work_mem = '512MB'  # For VACUUM, indexes
max_connections = 200
max_worker_processes = 8
max_parallel_workers_per_gather = 4

-- Write performance
wal_buffers = '16MB'
checkpoint_completion_target = 0.9
max_wal_size = '4GB'
min_wal_size = '1GB'

-- Query planning
random_page_cost = 1.1  # For SSD storage
effective_io_concurrency = 200  # For SSD
```

## API Performance

### Response Caching

```python
# Redis caching for API responses
from functools import wraps
from src.optimization.caching import CacheManager

cache = CacheManager()

def cached_response(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"api:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = await cache.get(cache_key)
            if cached:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Usage
@router.get("/ec-standards/{ec_clave}")
@cached_response(ttl=3600)
async def get_ec_standard(ec_clave: str):
    # Expensive database query
    return db.query(ECStandard).filter_by(ec_clave=ec_clave).first()
```

### Query Result Caching

```python
# Cache expensive aggregations
@cached_response(ttl=1800)
async def get_statistics():
    stats = {
        "total_ec": db.query(ECStandard).count(),
        "active_ec": db.query(ECStandard).filter_by(vigente=True).count(),
        "by_sector": db.query(
            ECStandard.sector_id,
            func.count(ECStandard.ec_clave)
        ).group_by(ECStandard.sector_id).all()
    }
    return stats
```

### Async Database Operations

```python
# Use async SQLAlchemy for better concurrency
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

async_engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=50,
    max_overflow=100
)

async def get_ec_async(ec_clave: str) -> ECStandard:
    async with AsyncSession(async_engine) as session:
        result = await session.execute(
            select(ECStandard).where(ECStandard.ec_clave == ec_clave)
        )
        return result.scalar_one_or_none()
```

## Redis Optimization

### Configuration

```redis
# redis.conf optimizations
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence settings (disable for cache-only)
save ""
appendonly no

# Network optimization
tcp-backlog 511
tcp-keepalive 60
timeout 300

# Performance
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
```

### Connection Pooling

```python
# Redis connection pool
import redis
from redis.connection import ConnectionPool

pool = ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=100,
    socket_keepalive=True,
    socket_keepalive_options={
        1: 1,  # TCP_KEEPIDLE
        2: 1,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    }
)

redis_client = redis.Redis(connection_pool=pool)
```

### Pipeline Operations

```python
# Use pipelines for bulk operations
def bulk_cache_set(items):
    pipe = redis_client.pipeline()
    for key, value, ttl in items:
        pipe.setex(key, ttl, json.dumps(value))
    pipe.execute()
```

## System Resource Optimization

### CPU Optimization

```python
# Use process pools for CPU-intensive tasks
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def process_data(data):
    # CPU-intensive processing
    return processed_data

# Use all available cores
with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
    results = list(executor.map(process_data, large_dataset))
```

### Memory Optimization

```python
# Stream processing for large datasets
def process_large_file(filepath):
    with open(filepath, 'r') as f:
        for line in f:  # Process line by line
            yield process_line(line)

# Use generators instead of lists
def get_all_items():
    for item in db.query(ECStandard).yield_per(1000):
        yield item.to_dict()
```

### Disk I/O Optimization

```python
# Async file operations
import aiofiles

async def write_export_async(data, filepath):
    async with aiofiles.open(filepath, 'w') as f:
        await f.write(json.dumps(data))

# Buffer writes
BUFFER_SIZE = 8192  # 8KB buffer

with open(filepath, 'w', buffering=BUFFER_SIZE) as f:
    for chunk in data_chunks:
        f.write(chunk)
```

## Monitoring and Profiling

### Performance Metrics

```python
# Custom metrics collection
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

spider_items = Counter(
    'spider_items_total',
    'Total items scraped',
    ['spider', 'item_type']
)

db_connections = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

# Use decorators for automatic tracking
def track_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with request_duration.labels(
            method=request.method,
            endpoint=request.endpoint
        ).time():
            return func(*args, **kwargs)
    return wrapper
```

### Query Analysis

```sql
-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT query, 
       mean_exec_time,
       calls,
       total_exec_time,
       min_exec_time,
       max_exec_time,
       stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Analyze specific query
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM ec_standards_v2 
WHERE sector_id = 1 AND vigente = true;
```

### Profiling Tools

```python
# Python profiling
import cProfile
import pstats
from io import StringIO

def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        # Print results
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        print(s.getvalue())
        
        return result
    return wrapper

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function code
    pass
```

## Load Testing

### API Load Testing

```python
# locustfile.py
from locust import HttpUser, task, between

class RenecAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_ec_standards(self):
        self.client.get("/api/v1/ec-standards?limit=100")
    
    @task(1)
    def get_ec_detail(self):
        ec_clave = "EC0217"
        self.client.get(f"/api/v1/ec-standards/{ec_clave}")
    
    @task(2)
    def search(self):
        self.client.get("/api/v1/search?q=tecnología")
```

Run load test:
```bash
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

## Optimization Checklist

### Before Deployment
- [ ] Database indexes analyzed and optimized
- [ ] Query performance tested
- [ ] Connection pools configured
- [ ] Caching strategy implemented
- [ ] Memory limits set appropriately
- [ ] CPU affinity configured
- [ ] Log levels set to production values
- [ ] Monitoring alerts configured

### Regular Maintenance
- [ ] Analyze slow query logs weekly
- [ ] Update table statistics (ANALYZE)
- [ ] Check index usage
- [ ] Review cache hit rates
- [ ] Monitor memory usage trends
- [ ] Profile hot code paths
- [ ] Update dependencies for performance fixes

### Performance Review
- [ ] Measure against targets
- [ ] Identify bottlenecks
- [ ] Test optimization changes
- [ ] Document improvements
- [ ] Update monitoring thresholds
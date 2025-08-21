"""
Tests for caching optimization module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from datetime import datetime

from src.optimization.caching import (
    CacheManager,
    cached,
    cached_api_response,
    invalidate_pattern,
    CacheStats
)


class TestCacheManager:
    """Test CacheManager functionality."""
    
    @patch('redis.from_url')
    def test_singleton_pattern(self, mock_redis_from_url):
        """Test CacheManager implements singleton pattern."""
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        
        manager1 = CacheManager()
        manager2 = CacheManager()
        
        assert manager1 is manager2
    
    @patch('redis.from_url')
    def test_get_set_operations(self, mock_redis_from_url):
        """Test basic get/set operations."""
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        
        manager = CacheManager()
        
        # Test set
        mock_redis.setex.return_value = True
        result = manager.set("test_key", {"data": "value"}, ttl=3600)
        assert result is True
        mock_redis.setex.assert_called_once()
        
        # Verify JSON serialization
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 3600
        assert json.loads(call_args[0][2]) == {"data": "value"}
        
        # Test get
        mock_redis.get.return_value = json.dumps({"data": "value"}).encode()
        result = manager.get("test_key")
        assert result == {"data": "value"}
    
    @patch('redis.from_url')
    def test_get_nonexistent_key(self, mock_redis_from_url):
        """Test getting non-existent key."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis_from_url.return_value = mock_redis
        
        manager = CacheManager()
        result = manager.get("nonexistent")
        assert result is None
    
    @patch('redis.from_url')
    def test_delete_operation(self, mock_redis_from_url):
        """Test delete operation."""
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        mock_redis_from_url.return_value = mock_redis
        
        manager = CacheManager()
        result = manager.delete("test_key")
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")
    
    @patch('redis.from_url')
    def test_exists_operation(self, mock_redis_from_url):
        """Test exists operation."""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1
        mock_redis_from_url.return_value = mock_redis
        
        manager = CacheManager()
        assert manager.exists("existing_key") is True
        
        mock_redis.exists.return_value = 0
        assert manager.exists("nonexistent_key") is False
    
    @patch('redis.from_url')
    def test_invalidate_pattern(self, mock_redis_from_url):
        """Test pattern-based invalidation."""
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3
        mock_redis_from_url.return_value = mock_redis
        
        manager = CacheManager()
        count = manager.invalidate_pattern("test:*")
        
        assert count == 3
        mock_redis.scan_iter.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")
    
    @patch('redis.from_url')
    def test_get_stats(self, mock_redis_from_url):
        """Test cache statistics."""
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        
        manager = CacheManager()
        
        # Simulate some operations
        mock_redis.get.return_value = json.dumps({"data": "value"}).encode()
        manager.get("hit_key")
        
        mock_redis.get.return_value = None
        manager.get("miss_key")
        
        stats = manager.get_stats()
        assert isinstance(stats, dict)
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestCachedDecorator:
    """Test cached decorator."""
    
    @patch('src.optimization.caching.CacheManager')
    def test_cached_function_hit(self, mock_cache_manager_class):
        """Test cached function with cache hit."""
        mock_manager = MagicMock()
        mock_manager.get.return_value = {"result": 42}
        mock_cache_manager_class.return_value = mock_manager
        
        @cached(ttl=3600, prefix="test")
        def expensive_function(x):
            return x * 2
        
        result = expensive_function(5)
        assert result == {"result": 42}
        
        # Verify cache was checked
        mock_manager.get.assert_called_once()
        # Function should not have been called
        mock_manager.set.assert_not_called()
    
    @patch('src.optimization.caching.CacheManager')
    def test_cached_function_miss(self, mock_cache_manager_class):
        """Test cached function with cache miss."""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_cache_manager_class.return_value = mock_manager
        
        @cached(ttl=3600, prefix="test")
        def expensive_function(x):
            return x * 2
        
        result = expensive_function(5)
        assert result == 10
        
        # Verify cache was checked and set
        mock_manager.get.assert_called_once()
        mock_manager.set.assert_called_once()
        
        # Verify correct value was cached
        cached_value = mock_manager.set.call_args[0][1]
        assert cached_value == 10
    
    @patch('src.optimization.caching.CacheManager')
    def test_cached_with_different_args(self, mock_cache_manager_class):
        """Test cached function generates different keys for different args."""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_cache_manager_class.return_value = mock_manager
        
        @cached(ttl=3600, prefix="test")
        def add(x, y):
            return x + y
        
        result1 = add(1, 2)
        result2 = add(3, 4)
        
        assert result1 == 3
        assert result2 == 7
        
        # Verify different cache keys were used
        calls = mock_manager.get.call_args_list
        assert len(calls) == 2
        key1 = calls[0][0][0]
        key2 = calls[1][0][0]
        assert key1 != key2


class TestCachedApiResponseDecorator:
    """Test cached_api_response decorator."""
    
    @patch('src.optimization.caching.CacheManager')
    def test_api_response_caching(self, mock_cache_manager_class):
        """Test API response caching."""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_cache_manager_class.return_value = mock_manager
        
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        @app.get("/test")
        @cached_api_response(ttl=300)
        def test_endpoint(param: str = "default"):
            return {"result": param, "timestamp": time.time()}
        
        client = TestClient(app)
        
        # First request - cache miss
        response1 = client.get("/test?param=value1")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Verify cache was set
        mock_manager.set.assert_called_once()
        
        # Second request with same param - should hit cache
        mock_manager.get.return_value = data1
        response2 = client.get("/test?param=value1")
        assert response2.status_code == 200
        assert response2.json() == data1
    
    @patch('src.optimization.caching.CacheManager')
    def test_api_response_skip_cache_header(self, mock_cache_manager_class):
        """Test API response skips cache with header."""
        mock_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_manager
        
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        @app.get("/test")
        @cached_api_response(ttl=300)
        def test_endpoint():
            return {"result": "data"}
        
        client = TestClient(app)
        
        # Request with skip-cache header
        response = client.get("/test", headers={"X-Skip-Cache": "true"})
        assert response.status_code == 200
        
        # Verify cache was not checked
        mock_manager.get.assert_not_called()


class TestInvalidatePattern:
    """Test invalidate_pattern function."""
    
    @patch('src.optimization.caching.CacheManager')
    def test_invalidate_pattern_function(self, mock_cache_manager_class):
        """Test pattern invalidation function."""
        mock_manager = MagicMock()
        mock_manager.invalidate_pattern.return_value = 5
        mock_cache_manager_class.return_value = mock_manager
        
        count = invalidate_pattern("api:ec:*")
        assert count == 5
        mock_manager.invalidate_pattern.assert_called_once_with("api:ec:*")


class TestCacheStats:
    """Test CacheStats class."""
    
    def test_cache_stats_initialization(self):
        """Test CacheStats initialization."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.errors == 0
    
    def test_cache_stats_hit_rate(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0
        
        stats.hits = 3
        stats.misses = 1
        assert stats.hit_rate == 0.75
        
        stats.hits = 0
        stats.misses = 0
        assert stats.hit_rate == 0.0
    
    def test_cache_stats_to_dict(self):
        """Test conversion to dictionary."""
        stats = CacheStats()
        stats.hits = 10
        stats.misses = 5
        stats.sets = 5
        
        data = stats.to_dict()
        assert data["hits"] == 10
        assert data["misses"] == 5
        assert data["sets"] == 5
        assert data["hit_rate"] == 2/3  # 10/(10+5)
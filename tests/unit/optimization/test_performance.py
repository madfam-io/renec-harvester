"""
Tests for performance optimization module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time
from datetime import datetime, timedelta

from src.optimization.performance import (
    PerformanceMonitor,
    BatchProcessor,
    ConnectionPool,
    QueryOptimizer,
    ResourceThrottler,
    measure_performance,
    optimize_query
)


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality."""
    
    def test_singleton_pattern(self):
        """Test PerformanceMonitor implements singleton pattern."""
        monitor1 = PerformanceMonitor()
        monitor2 = PerformanceMonitor()
        assert monitor1 is monitor2
    
    def test_start_end_operation(self):
        """Test operation timing."""
        monitor = PerformanceMonitor()
        
        # Start operation
        monitor.start_operation("test_op", {"param": "value"})
        
        # Simulate some work
        time.sleep(0.1)
        
        # End operation
        duration = monitor.end_operation("test_op")
        
        assert duration >= 0.1
        assert "test_op" in monitor.metrics
        assert monitor.metrics["test_op"]["count"] == 1
        assert monitor.metrics["test_op"]["total_time"] >= 0.1
    
    def test_record_metric(self):
        """Test recording custom metrics."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric("db_queries", 5)
        monitor.record_metric("db_queries", 3)
        monitor.record_metric("cache_hits", 10)
        
        assert monitor.metrics["db_queries"]["count"] == 2
        assert monitor.metrics["db_queries"]["total"] == 8
        assert monitor.metrics["cache_hits"]["count"] == 1
        assert monitor.metrics["cache_hits"]["total"] == 10
    
    def test_get_stats(self):
        """Test getting performance statistics."""
        monitor = PerformanceMonitor()
        
        # Record some operations
        monitor.start_operation("api_request", {})
        time.sleep(0.05)
        monitor.end_operation("api_request")
        
        monitor.start_operation("api_request", {})
        time.sleep(0.15)
        monitor.end_operation("api_request")
        
        stats = monitor.get_stats()
        
        assert "api_request" in stats
        assert stats["api_request"]["count"] == 2
        assert stats["api_request"]["avg_time"] >= 0.1
        assert stats["api_request"]["min_time"] >= 0.05
        assert stats["api_request"]["max_time"] >= 0.15
    
    def test_reset_metrics(self):
        """Test resetting metrics."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric("test_metric", 100)
        assert len(monitor.metrics) > 0
        
        monitor.reset()
        assert len(monitor.metrics) == 0


class TestBatchProcessor:
    """Test BatchProcessor functionality."""
    
    def test_batch_processing(self):
        """Test basic batch processing."""
        processor = BatchProcessor(batch_size=3)
        
        processed_batches = []
        
        def process_func(batch):
            processed_batches.append(batch)
        
        # Add items
        processor.add_item(1, process_func)
        processor.add_item(2, process_func)
        processor.add_item(3, process_func)  # Should trigger batch
        
        assert len(processed_batches) == 1
        assert processed_batches[0] == [1, 2, 3]
        
        # Add more items
        processor.add_item(4, process_func)
        processor.add_item(5, process_func)
        
        # Flush remaining
        processor.flush()
        
        assert len(processed_batches) == 2
        assert processed_batches[1] == [4, 5]
    
    def test_timeout_processing(self):
        """Test batch processing with timeout."""
        processor = BatchProcessor(batch_size=10, timeout=0.1)
        
        processed = []
        
        def process_func(batch):
            processed.extend(batch)
        
        # Add items but don't reach batch size
        processor.add_item(1, process_func)
        processor.add_item(2, process_func)
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Add another item - should trigger timeout processing
        processor.add_item(3, process_func)
        
        assert 1 in processed
        assert 2 in processed
    
    def test_different_processors(self):
        """Test handling different processor functions."""
        processor = BatchProcessor(batch_size=2)
        
        results_a = []
        results_b = []
        
        def process_a(batch):
            results_a.extend(batch)
        
        def process_b(batch):
            results_b.extend(batch)
        
        processor.add_item("A1", process_a)
        processor.add_item("B1", process_b)
        processor.add_item("A2", process_a)  # Should trigger batch for A
        processor.add_item("B2", process_b)  # Should trigger batch for B
        
        assert results_a == ["A1", "A2"]
        assert results_b == ["B1", "B2"]


class TestConnectionPool:
    """Test ConnectionPool functionality."""
    
    def test_connection_acquisition(self):
        """Test getting and releasing connections."""
        def create_conn():
            return Mock(id=id(Mock()))
        
        pool = ConnectionPool(create_conn, max_size=2)
        
        # Get connection
        conn1 = pool.get_connection()
        assert conn1 is not None
        
        # Get another
        conn2 = pool.get_connection()
        assert conn2 is not None
        assert conn1 is not conn2
        
        # Pool should be empty now
        conn3 = pool.get_connection(timeout=0.1)
        assert conn3 is None
        
        # Release one
        pool.release_connection(conn1)
        
        # Should be able to get it again
        conn4 = pool.get_connection()
        assert conn4 is conn1
    
    def test_context_manager(self):
        """Test connection pool context manager."""
        def create_conn():
            return Mock()
        
        pool = ConnectionPool(create_conn, max_size=1)
        
        # Use connection in context
        with pool.get_connection_context() as conn:
            assert conn is not None
            # Connection should not be available
            assert pool.get_connection(timeout=0.1) is None
        
        # Connection should be released
        conn2 = pool.get_connection()
        assert conn2 is not None
    
    def test_connection_validation(self):
        """Test connection validation."""
        def create_conn():
            return Mock(is_valid=True)
        
        def validate_conn(conn):
            return conn.is_valid
        
        pool = ConnectionPool(create_conn, max_size=2, validate_func=validate_conn)
        
        # Get connection
        conn = pool.get_connection()
        assert conn is not None
        
        # Invalidate and release
        conn.is_valid = False
        pool.release_connection(conn)
        
        # Should create new connection
        new_conn = pool.get_connection()
        assert new_conn is not conn
        assert new_conn.is_valid is True


class TestQueryOptimizer:
    """Test QueryOptimizer functionality."""
    
    @patch('src.optimization.performance.get_session')
    def test_query_analysis(self, mock_get_session):
        """Test query analysis and optimization."""
        # Mock session and query
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        optimizer = QueryOptimizer()
        
        # Analyze query
        from sqlalchemy import select, column, table
        test_table = table('test_table', column('id'), column('name'))
        query = select([test_table]).where(test_table.c.name == 'test')
        
        analysis = optimizer.analyze_query(query)
        
        assert isinstance(analysis, dict)
        assert "tables" in analysis
        assert "has_where" in analysis
    
    def test_optimize_pagination(self):
        """Test pagination optimization."""
        optimizer = QueryOptimizer()
        
        # Mock query
        mock_query = Mock()
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        
        # Optimize for pagination
        optimized = optimizer.optimize_for_pagination(mock_query, page=2, page_size=20)
        
        mock_query.limit.assert_called_with(20)
        mock_query.offset.assert_called_with(20)  # (page-1) * page_size
    
    def test_add_indexes(self):
        """Test index suggestion."""
        optimizer = QueryOptimizer()
        
        # Mock query with frequent filters
        optimizer.query_stats["table1.column1"] = {"count": 100, "avg_time": 0.5}
        optimizer.query_stats["table2.column2"] = {"count": 50, "avg_time": 0.3}
        
        suggestions = optimizer.suggest_indexes()
        
        assert len(suggestions) > 0
        assert any("table1.column1" in s for s in suggestions)


class TestResourceThrottler:
    """Test ResourceThrottler functionality."""
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        throttler = ResourceThrottler(rate_limit=5, window=1)  # 5 per second
        
        # Should allow first 5
        for i in range(5):
            assert throttler.should_throttle() is False
        
        # Should throttle 6th
        assert throttler.should_throttle() is True
        
        # Wait and try again
        time.sleep(1.1)
        assert throttler.should_throttle() is False
    
    def test_cpu_throttling(self):
        """Test CPU-based throttling."""
        throttler = ResourceThrottler(cpu_threshold=80)
        
        # Mock CPU usage
        with patch('psutil.cpu_percent', return_value=85):
            assert throttler.should_throttle() is True
        
        with patch('psutil.cpu_percent', return_value=70):
            assert throttler.should_throttle() is False
    
    def test_memory_throttling(self):
        """Test memory-based throttling."""
        throttler = ResourceThrottler(memory_threshold=90)
        
        # Mock memory usage
        mock_memory = Mock()
        mock_memory.percent = 95
        
        with patch('psutil.virtual_memory', return_value=mock_memory):
            assert throttler.should_throttle() is True
        
        mock_memory.percent = 85
        with patch('psutil.virtual_memory', return_value=mock_memory):
            assert throttler.should_throttle() is False
    
    def test_adaptive_throttling(self):
        """Test adaptive throttling based on response times."""
        throttler = ResourceThrottler(adaptive=True)
        
        # Record fast response times
        for _ in range(5):
            throttler.record_response_time(0.05)
        
        assert throttler.get_delay() < 0.1
        
        # Record slow response times
        for _ in range(5):
            throttler.record_response_time(2.0)
        
        assert throttler.get_delay() > 0.5


class TestMeasurePerformanceDecorator:
    """Test measure_performance decorator."""
    
    @patch('src.optimization.performance.PerformanceMonitor')
    def test_performance_measurement(self, mock_monitor_class):
        """Test function performance measurement."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        @measure_performance("test_operation")
        def slow_function(x):
            time.sleep(0.1)
            return x * 2
        
        result = slow_function(5)
        assert result == 10
        
        # Verify monitoring
        mock_monitor.start_operation.assert_called_once()
        mock_monitor.end_operation.assert_called_once()
        
        # Check operation name
        call_args = mock_monitor.start_operation.call_args
        assert call_args[0][0] == "test_operation"
    
    @patch('src.optimization.performance.PerformanceMonitor')
    def test_performance_measurement_with_error(self, mock_monitor_class):
        """Test performance measurement when function raises error."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        @measure_performance("error_operation")
        def error_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            error_function()
        
        # Should still record the operation
        mock_monitor.start_operation.assert_called_once()
        mock_monitor.end_operation.assert_called_once()


class TestOptimizeQueryDecorator:
    """Test optimize_query decorator."""
    
    def test_query_optimization(self):
        """Test query optimization decorator."""
        @optimize_query
        def get_data(query):
            return query.all()
        
        # Mock query
        mock_query = Mock()
        mock_query.all.return_value = ["result1", "result2"]
        
        result = get_data(mock_query)
        assert result == ["result1", "result2"]
        
        # Verify query methods were called (basic optimization)
        # The decorator should analyze but not modify in this simple case
        assert mock_query.all.called
"""
End-to-end tests for full harvest process.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os
from datetime import datetime
from pathlib import Path

from src.cli.commands import crawl, harvest, validate, diff, publish
from src.export.exporter import Exporter


class TestFullHarvest:
    """Test complete end-to-end harvest process."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            Path(f"{tmpdir}/artifacts").mkdir()
            Path(f"{tmpdir}/logs").mkdir()
            Path(f"{tmpdir}/data").mkdir()
            yield tmpdir
    
    @pytest.fixture
    def mock_spider_run(self):
        """Mock successful spider run."""
        with patch('scrapy.crawler.CrawlerProcess') as mock_crawler:
            mock_process = MagicMock()
            mock_crawler.return_value = mock_process
            
            # Mock spider stats
            mock_stats = {
                "item_scraped_count": 1500,
                "response_received_count": 200,
                "downloader/request_count": 250,
                "finish_time": datetime.utcnow(),
                "start_time": datetime.utcnow()
            }
            mock_process.crawlers = [Mock(stats=Mock(get_stats=Mock(return_value=mock_stats)))]
            
            yield mock_process
    
    @patch('src.cli.commands.CrawlerProcess')
    def test_full_crawl_command(self, mock_crawler_class, temp_workspace):
        """Test full crawl command execution."""
        mock_process = MagicMock()
        mock_crawler_class.return_value = mock_process
        
        # Execute crawl
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            crawl(max_depth=3, concurrent=5)
        
        # Verify crawler was configured correctly
        mock_crawler_class.assert_called_once()
        settings = mock_crawler_class.call_args[0][0]
        assert settings['CONCURRENT_REQUESTS'] == 5
        assert settings['DEPTH_LIMIT'] == 3
    
    @patch('src.cli.commands.CrawlerProcess')
    @patch('src.cli.commands.get_session')
    def test_full_harvest_command(self, mock_get_session, mock_crawler_class, temp_workspace):
        """Test full harvest command execution."""
        # Mock crawler
        mock_process = MagicMock()
        mock_crawler_class.return_value = mock_process
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock query results
        mock_session.query.return_value.count.return_value = 1500
        
        # Execute harvest
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            harvest(force=False)
        
        # Verify harvest was executed
        mock_process.crawl.assert_called_once()
        mock_process.start.assert_called_once()
    
    def test_validate_command(self, temp_workspace):
        """Test validate command execution."""
        # Create test harvest file
        harvest_data = {
            "metadata": {
                "harvest_date": datetime.utcnow().isoformat(),
                "total_records": 1500
            },
            "ec_standards": [
                {"ec_clave": "EC0217", "titulo": "Test", "vigente": True}
            ]
        }
        
        harvest_file = f"{temp_workspace}/harvest_20240121.json"
        with open(harvest_file, 'w') as f:
            json.dump(harvest_data, f)
        
        # Execute validate
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            result = validate(harvest_file)
        
        assert result is True
    
    def test_diff_command(self, temp_workspace):
        """Test diff command execution."""
        # Create two harvest files
        old_data = {
            "metadata": {"harvest_date": "2024-01-20"},
            "ec_standards": [
                {"ec_clave": "EC0217", "titulo": "Old Title", "vigente": True}
            ]
        }
        
        new_data = {
            "metadata": {"harvest_date": "2024-01-21"},
            "ec_standards": [
                {"ec_clave": "EC0217", "titulo": "New Title", "vigente": True},
                {"ec_clave": "EC0435", "titulo": "New Standard", "vigente": True}
            ]
        }
        
        old_file = f"{temp_workspace}/harvest_20240120.json"
        new_file = f"{temp_workspace}/harvest_20240121.json"
        
        with open(old_file, 'w') as f:
            json.dump(old_data, f)
        with open(new_file, 'w') as f:
            json.dump(new_data, f)
        
        # Execute diff
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            diff_file = diff(old_file, new_file)
        
        assert Path(diff_file).exists()
        
        # Verify diff content
        with open(diff_file, 'r') as f:
            diff_content = f.read()
        
        assert "Modified" in diff_content
        assert "EC0217" in diff_content
        assert "Added" in diff_content
        assert "EC0435" in diff_content
    
    @patch('subprocess.run')
    def test_publish_command(self, mock_subprocess, temp_workspace):
        """Test publish command execution."""
        # Create test files
        files = [
            f"{temp_workspace}/harvest_20240121.json",
            f"{temp_workspace}/harvest_20240121.db",
            f"{temp_workspace}/harvest_20240121.csv"
        ]
        
        for file in files:
            Path(file).touch()
        
        # Execute publish
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            with patch.dict(os.environ, {'S3_BUCKET': 'test-bucket'}):
                publish(files, s3_bucket='test-bucket')
        
        # Verify S3 upload was called
        assert mock_subprocess.called
        call_args = mock_subprocess.call_args[0][0]
        assert 'aws' in call_args
        assert 's3' in call_args
        assert 'cp' in call_args
    
    @patch('src.cli.commands.CrawlerProcess')
    @patch('src.export.exporter.get_session')
    def test_complete_workflow(self, mock_get_session, mock_crawler_class, temp_workspace):
        """Test complete harvest workflow from crawl to export."""
        # Setup mocks
        mock_process = MagicMock()
        mock_crawler_class.return_value = mock_process
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock data
        mock_ec = Mock()
        mock_ec.ec_clave = "EC0217"
        mock_ec.titulo = "Test Standard"
        mock_ec.to_dict.return_value = {
            "ec_clave": "EC0217",
            "titulo": "Test Standard"
        }
        
        mock_query = Mock()
        mock_query.all.return_value = [mock_ec]
        mock_query.count.return_value = 1
        mock_session.query.return_value = mock_query
        
        # 1. Crawl
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            crawl(max_depth=5)
        
        # 2. Harvest
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            harvest()
        
        # 3. Export
        exporter = Exporter()
        output_file = f"{temp_workspace}/harvest_test.json"
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            exporter.export_json(output_file, ["ec_standard"])
            
            # Verify export was called
            mock_open.assert_called()
            assert mock_file.write.called
    
    def test_error_handling_workflow(self, temp_workspace):
        """Test error handling in workflow."""
        # Test with missing crawl map
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            with pytest.raises(FileNotFoundError):
                harvest(require_crawl_map=True)
        
        # Test with invalid harvest file
        invalid_file = f"{temp_workspace}/invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json{")
        
        with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
            result = validate(invalid_file)
            assert result is False
    
    def test_performance_metrics(self, mock_spider_run, temp_workspace):
        """Test performance metrics collection."""
        from src.optimization.performance import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        monitor.reset()
        
        # Simulate harvest with metrics
        with patch('src.cli.commands.CrawlerProcess', return_value=mock_spider_run):
            with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
                # Track crawl performance
                monitor.start_operation("crawl", {"max_depth": 5})
                crawl(max_depth=5)
                crawl_time = monitor.end_operation("crawl")
                
                # Track harvest performance
                monitor.start_operation("harvest", {})
                harvest()
                harvest_time = monitor.end_operation("harvest")
        
        # Verify metrics
        stats = monitor.get_stats()
        assert "crawl" in stats
        assert "harvest" in stats
        assert stats["crawl"]["count"] == 1
        assert stats["harvest"]["count"] == 1
    
    def test_data_freshness_check(self, temp_workspace):
        """Test data freshness validation."""
        # Create harvest with old data
        old_harvest = {
            "metadata": {
                "harvest_date": "2023-01-01T00:00:00"
            },
            "ec_standards": []
        }
        
        harvest_file = f"{temp_workspace}/old_harvest.json"
        with open(harvest_file, 'w') as f:
            json.dump(old_harvest, f)
        
        # Check freshness
        with open(harvest_file, 'r') as f:
            data = json.load(f)
        
        harvest_date = datetime.fromisoformat(data["metadata"]["harvest_date"])
        age_days = (datetime.utcnow() - harvest_date).days
        
        assert age_days > 30  # Data is stale
    
    def test_incremental_harvest(self, temp_workspace):
        """Test incremental harvest functionality."""
        # Create previous harvest
        prev_harvest = {
            "metadata": {
                "harvest_date": datetime.utcnow().isoformat(),
                "total_records": 1000
            },
            "ec_standards": [
                {"ec_clave": "EC0001", "titulo": "Existing", "last_seen": "2024-01-20"}
            ]
        }
        
        prev_file = f"{temp_workspace}/harvest_previous.json"
        with open(prev_file, 'w') as f:
            json.dump(prev_harvest, f)
        
        # Mock incremental harvest
        with patch('src.cli.commands.get_last_harvest_date') as mock_last_date:
            mock_last_date.return_value = datetime(2024, 1, 20)
            
            with patch('src.cli.commands.CrawlerProcess') as mock_crawler:
                mock_process = MagicMock()
                mock_crawler.return_value = mock_process
                
                with patch('src.cli.commands.ARTIFACTS_DIR', temp_workspace):
                    harvest(incremental=True)
                
                # Verify incremental mode was used
                crawl_args = mock_process.crawl.call_args
                assert 'since_date' in crawl_args[1]
"""Unit tests for Scrapy pipelines."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from scrapy.exceptions import DropItem

from src.discovery.pipelines import (
    ValidationPipeline,
    NormalizationPipeline,
    DeduplicationPipeline,
    DatabasePipeline,
    CachePipeline,
)


class TestValidationPipeline:
    """Test cases for ValidationPipeline."""
    
    def test_validate_ec_standard_valid(self):
        """Test validation of valid EC standard."""
        pipeline = ValidationPipeline()
        
        item = {
            "type": "ec_standard",
            "code": "EC0001",
            "title": "Competencia en desarrollo de software",
            "level": 3,
        }
        
        result = pipeline.process_item(item, None)
        assert "validation_errors" not in result
    
    def test_validate_ec_standard_invalid(self):
        """Test validation of invalid EC standard."""
        pipeline = ValidationPipeline()
        
        item = {
            "type": "ec_standard",
            "code": "INVALID",  # Invalid format
            "title": "",  # Empty title
            "level": "invalid",  # Non-integer level
        }
        
        result = pipeline.process_item(item, None)
        assert "validation_errors" in result
        assert len(result["validation_errors"]) >= 2
        
        # Check specific errors
        error_fields = [e["field"] for e in result["validation_errors"]]
        assert "code" in error_fields
        assert "title" in error_fields
    
    def test_validate_certificador_valid(self):
        """Test validation of valid certificador."""
        pipeline = ValidationPipeline()
        
        item = {
            "type": "certificador",
            "code": "OC001",
            "name": "Centro Certificador",
            "contact_email": "contacto@certificador.mx",
            "rfc": "CCT123456ABC",
        }
        
        result = pipeline.process_item(item, None)
        assert "validation_errors" not in result
    
    def test_validate_certificador_invalid_email(self):
        """Test validation of certificador with invalid email."""
        pipeline = ValidationPipeline()
        
        item = {
            "type": "certificador",
            "code": "OC001",
            "name": "Centro Certificador",
            "contact_email": "invalid-email",  # Invalid email format
        }
        
        result = pipeline.process_item(item, None)
        assert "validation_errors" in result
        
        error = next(e for e in result["validation_errors"] if e["field"] == "contact_email")
        assert "Invalid email" in error["error"]
    
    def test_validate_missing_type(self):
        """Test validation of item without type."""
        pipeline = ValidationPipeline()
        
        item = {"code": "EC0001", "title": "Test"}
        
        with pytest.raises(DropItem, match="Missing item type"):
            pipeline.process_item(item, None)


class TestNormalizationPipeline:
    """Test cases for NormalizationPipeline."""
    
    def test_normalize_common_fields(self):
        """Test normalization of common fields."""
        pipeline = NormalizationPipeline()
        
        item = {
            "type": "certificador",
            "name": "  Centro Certificador  ",  # Extra spaces
            "contact_email": "CONTACTO@CERT.MX",  # Uppercase
            "contact_phone": "55-5555-5555",  # Needs normalization
            "url": "https://example.com/page/",  # Trailing slash
        }
        
        result = pipeline.process_item(item, None)
        
        assert result["name"] == "Centro Certificador"
        assert result["contact_email"] == "contacto@cert.mx"
        assert result["url"] == "https://example.com/page"
        assert "content_hash" in result
        assert "normalized_at" in result
    
    def test_normalize_phone_number(self):
        """Test phone number normalization."""
        pipeline = NormalizationPipeline()
        
        # Test Mexican phone number
        assert pipeline._normalize_phone("5555555555") == "+525555555555"
        assert pipeline._normalize_phone("52 555 555 5555") == "+525555555555"
        assert pipeline._normalize_phone("+525555555555") == "+525555555555"
        
        # Test invalid phone
        assert pipeline._normalize_phone("123") == "123"  # Return original if can't normalize
    
    def test_normalize_state_names(self):
        """Test Mexican state name normalization."""
        pipeline = NormalizationPipeline()
        
        assert pipeline._normalize_state("cdmx") == "Ciudad de México"
        assert pipeline._normalize_state("CDMX") == "Ciudad de México"
        assert pipeline._normalize_state("mexico") == "Estado de México"
        assert pipeline._normalize_state("NL") == "Nuevo León"
        assert pipeline._normalize_state("Jalisco") == "Jalisco"  # Already normalized
    
    def test_normalize_ec_standard(self):
        """Test EC standard specific normalization."""
        pipeline = NormalizationPipeline()
        
        item = {
            "type": "ec_standard",
            "code": "ec0001",  # Lowercase
            "sector": "tecnología",  # Needs title case
            "publication_date": "2023-01-15",  # String date
        }
        
        result = pipeline.process_item(item, None)
        
        assert result["code"] == "EC0001"
        assert result["sector"] == "Tecnología"
        # Date parsing is attempted but may remain as string
    
    def test_normalize_course_modality(self):
        """Test course modality normalization."""
        pipeline = NormalizationPipeline()
        
        item1 = {"type": "course", "modality": "En línea"}
        result1 = pipeline.process_item(item1, None)
        assert result1["modality"] == "en_linea"
        
        item2 = {"type": "course", "modality": "PRESENCIAL"}
        result2 = pipeline.process_item(item2, None)
        assert result2["modality"] == "presencial"
        
        item3 = {"type": "course", "modality": "Híbrido"}
        result3 = pipeline.process_item(item3, None)
        assert result3["modality"] == "mixto"


class TestDeduplicationPipeline:
    """Test cases for DeduplicationPipeline."""
    
    @patch("redis.from_url")
    def test_deduplication_new_item(self, mock_redis_from_url):
        """Test processing new item."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.exists.return_value = False
        mock_redis.setex.return_value = True
        mock_redis_from_url.return_value = mock_redis
        
        pipeline = DeduplicationPipeline(redis_url="redis://localhost:6379")
        pipeline.open_spider(None)
        
        item = {
            "type": "ec_standard",
            "content_hash": "abc123",
        }
        
        result = pipeline.process_item(item, None)
        
        assert result == item
        mock_redis.exists.assert_called_once_with("dedup:ec_standard:abc123")
        mock_redis.setex.assert_called_once()
    
    @patch("redis.from_url")
    def test_deduplication_duplicate_item(self, mock_redis_from_url):
        """Test dropping duplicate item."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.exists.return_value = True
        mock_redis_from_url.return_value = mock_redis
        
        pipeline = DeduplicationPipeline(redis_url="redis://localhost:6379")
        pipeline.open_spider(None)
        
        item = {
            "type": "ec_standard",
            "content_hash": "abc123",
        }
        
        with pytest.raises(DropItem, match="Duplicate item found in Redis"):
            pipeline.process_item(item, None)
    
    def test_deduplication_local_cache(self):
        """Test local cache deduplication."""
        pipeline = DeduplicationPipeline(redis_url="redis://localhost:6379")
        
        # Add to local cache
        pipeline.seen_items.add("dedup:ec_standard:abc123")
        
        item = {
            "type": "ec_standard",
            "content_hash": "abc123",
        }
        
        with pytest.raises(DropItem, match="Duplicate item"):
            pipeline.process_item(item, None)


class TestDatabasePipeline:
    """Test cases for DatabasePipeline."""
    
    def test_skip_items_with_validation_errors(self):
        """Test that items with validation errors are skipped."""
        pipeline = DatabasePipeline()
        
        item = {
            "type": "ec_standard",
            "validation_errors": [{"field": "code", "error": "Invalid"}],
        }
        
        result = pipeline.process_item(item, None)
        assert result == item  # Item returned unchanged
        assert pipeline.stats["saved"] == 0
    
    @patch("src.discovery.pipelines.get_session")
    def test_save_new_ec_standard(self, mock_get_session):
        """Test saving new EC standard."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query().filter_by().first.return_value = None  # No existing
        
        pipeline = DatabasePipeline()
        
        item = {
            "type": "ec_standard",
            "code": "EC0001",
            "title": "Test EC",
            "sector": "Technology",
            "level": 3,
        }
        
        result = pipeline.process_item(item, None)
        
        assert result == item
        assert pipeline.stats["saved"] == 1
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch("src.discovery.pipelines.get_session")
    def test_update_existing_ec_standard(self, mock_get_session):
        """Test updating existing EC standard."""
        # Mock existing EC standard
        mock_ec = MagicMock()
        mock_ec.code = "EC0001"
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query().filter_by().first.return_value = mock_ec
        
        pipeline = DatabasePipeline()
        
        item = {
            "type": "ec_standard",
            "code": "EC0001",
            "title": "Updated Title",
            "sector": "Updated Sector",
        }
        
        result = pipeline.process_item(item, None)
        
        assert result == item
        assert mock_ec.title == "Updated Title"
        assert mock_ec.sector == "Updated Sector"
        mock_session.commit.assert_called_once()


class TestCachePipeline:
    """Test cases for CachePipeline."""
    
    @patch("redis.from_url")
    def test_cache_item(self, mock_redis_from_url):
        """Test caching an item."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis_from_url.return_value = mock_redis
        
        pipeline = CachePipeline(redis_url="redis://localhost:6379")
        pipeline.open_spider(None)
        
        item = {
            "type": "ec_standard",
            "code": "EC0001",
            "title": "Test EC",
        }
        
        result = pipeline.process_item(item, None)
        
        assert result == item
        mock_redis.setex.assert_called_once()
        
        # Check cache key
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "cache:ec:EC0001"
        assert call_args[0][1] == 3600  # Default TTL
    
    def test_cache_skip_invalid_items(self):
        """Test that items without proper type/code are skipped."""
        pipeline = CachePipeline(redis_url="redis://localhost:6379")
        pipeline.redis_client = MagicMock()
        
        # Item without code
        item1 = {"type": "ec_standard", "title": "Test"}
        result1 = pipeline.process_item(item1, None)
        assert result1 == item1
        pipeline.redis_client.setex.assert_not_called()
        
        # Item with unknown type
        item2 = {"type": "unknown", "code": "CODE001"}
        result2 = pipeline.process_item(item2, None)
        assert result2 == item2
        pipeline.redis_client.setex.assert_not_called()
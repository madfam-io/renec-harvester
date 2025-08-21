"""
Tests for Sectores driver.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
from scrapy.http import HtmlResponse, Request

from src.drivers.sectores_driver import SectoresDriver


class TestSectoresDriver:
    """Test Sectores driver functionality."""
    
    @pytest.fixture
    def driver(self):
        """Create driver instance."""
        driver = SectoresDriver()
        driver.stats = {"parsed": 0, "errors": 0}
        return driver
    
    @pytest.fixture
    def mock_response(self):
        """Create mock Scrapy response."""
        response = Mock(spec=HtmlResponse)
        response.url = "https://conocer.gob.mx/test"
        response.status = 200
        response.css = Mock()
        response.xpath = Mock()
        response.meta = {}
        return response
    
    def test_parse_sector_list(self, driver, mock_response):
        """Test parsing sector list page."""
        # Mock sector cards
        mock_sector1 = Mock()
        mock_sector1.css.return_value.get.side_effect = [
            "/sector/1",  # Link
            "Tecnologías de la Información",  # Name
            "Sector dedicado al desarrollo de TI"  # Description
        ]
        mock_sector1.css.return_value.getall.return_value = ["5 comités", "50 estándares"]
        
        mock_sector2 = Mock()
        mock_sector2.css.return_value.get.side_effect = [
            "/sector/2",  # Link
            "Turismo",  # Name
            "Sector de servicios turísticos"  # Description
        ]
        mock_sector2.css.return_value.getall.return_value = ["8 comités", "80 estándares"]
        
        mock_response.css.return_value = [mock_sector1, mock_sector2]
        
        # Execute
        results = list(driver.parse_sector_list(mock_response))
        
        # Verify data items
        data_items = [r for r in results if isinstance(r, dict)]
        assert len(data_items) == 2
        assert data_items[0]["type"] == "sector"
        assert data_items[0]["sector_id"] == 1
        assert data_items[0]["nombre"] == "Tecnologías de la Información"
        assert data_items[0]["num_comites"] == 5
        assert data_items[0]["num_estandares"] == 50
        
        # Verify requests
        requests = [r for r in results if isinstance(r, Request)]
        assert len(requests) == 2
        assert requests[0].meta["sector_id"] == 1
    
    def test_parse_sector_detail(self, driver, mock_response):
        """Test parsing sector detail page."""
        mock_response.meta = {"sector_id": 1}
        
        # Mock sector info
        mock_response.css.return_value.get.side_effect = [
            "Tecnologías de la Información",  # Title
            "2010-01-15",  # Creation date
            "Sector enfocado en desarrollo y gestión de TI"  # Description
        ]
        
        # Mock comités
        mock_comite1 = Mock()
        mock_comite1.css.return_value.get.side_effect = [
            "/comite/101",
            "Desarrollo de Software"
        ]
        
        mock_comite2 = Mock()
        mock_comite2.css.return_value.get.side_effect = [
            "/comite/102",
            "Infraestructura TI"
        ]
        
        # Setup mock to return comites when .comite-card selector is used
        def mock_css(selector):
            if selector == ".comite-card":
                return [mock_comite1, mock_comite2]
            return Mock(get=Mock(return_value=None))
        
        mock_response.css = mock_css
        
        # Execute
        results = list(driver.parse_sector_detail(mock_response))
        
        # Verify
        assert len(results) == 2  # 2 requests for comités
        assert all(isinstance(r, Request) for r in results)
        assert results[0].meta["comite_id"] == 101
        assert results[0].meta["sector_id"] == 1
    
    def test_parse_comite_detail(self, driver, mock_response):
        """Test parsing comité detail page."""
        mock_response.meta = {
            "comite_id": 101,
            "sector_id": 1
        }
        
        # Mock comité info
        def mock_css_get(selector):
            mapping = {
                "h1::text": "Desarrollo de Software",
                ".description::text": "Comité para estándares de desarrollo",
                ".creation-date::text": "2012-06-01",
                ".num-standards::text": "15 estándares"
            }
            return mapping.get(selector)
        
        mock_response.css.return_value.get.side_effect = mock_css_get
        
        # Mock EC standards
        mock_ec1 = Mock()
        mock_ec1.css.return_value.get.side_effect = [
            "EC0217",
            "Impartición de cursos"
        ]
        
        mock_ec2 = Mock()
        mock_ec2.css.return_value.get.side_effect = [
            "EC0435",
            "Prestación de servicios"
        ]
        
        # Setup mock for EC standards
        def mock_css(selector):
            if selector == ".ec-standard":
                return [mock_ec1, mock_ec2]
            return Mock(get=Mock(side_effect=mock_css_get))
        
        mock_response.css = mock_css
        
        # Execute
        results = list(driver.parse_comite_detail(mock_response))
        
        # Verify comité data
        comite_items = [r for r in results if r["type"] == "comite"]
        assert len(comite_items) == 1
        assert comite_items[0]["comite_id"] == 101
        assert comite_items[0]["nombre"] == "Desarrollo de Software"
        assert comite_items[0]["sector_id"] == 1
        assert comite_items[0]["num_estandares"] == 15
        
        # Verify EC-sector relations
        relations = [r for r in results if r["type"] == "ec_sector"]
        assert len(relations) == 2
        assert relations[0]["ec_clave"] == "EC0217"
        assert relations[0]["sector_id"] == 1
    
    def test_extract_sector_id(self, driver):
        """Test sector ID extraction from URL."""
        assert driver.extract_sector_id("/sector/1") == 1
        assert driver.extract_sector_id("/RENEC/sector.do?id=5") == 5
        assert driver.extract_sector_id("https://conocer.gob.mx/sector/10") == 10
        assert driver.extract_sector_id("/invalid/url") is None
    
    def test_extract_comite_id(self, driver):
        """Test comité ID extraction from URL."""
        assert driver.extract_comite_id("/comite/101") == 101
        assert driver.extract_comite_id("/RENEC/comite.do?id=205") == 205
        assert driver.extract_comite_id("https://conocer.gob.mx/comite/300") == 300
        assert driver.extract_comite_id("/invalid/url") is None
    
    def test_parse_date(self, driver):
        """Test date parsing."""
        # Test various date formats
        assert driver.parse_date("2023-01-15") == date(2023, 1, 15)
        assert driver.parse_date("15/01/2023") == date(2023, 1, 15)
        assert driver.parse_date("15-01-2023") == date(2023, 1, 15)
        assert driver.parse_date("invalid date") is None
        assert driver.parse_date("") is None
    
    def test_extract_number(self, driver):
        """Test number extraction from text."""
        assert driver.extract_number("15 estándares") == 15
        assert driver.extract_number("Total: 100 items") == 100
        assert driver.extract_number("No numbers here") == 0
        assert driver.extract_number("") == 0
    
    def test_parse_sector_ec_standards(self, driver, mock_response):
        """Test parsing sector EC standards page."""
        mock_response.meta = {"sector_id": 1}
        
        # Mock EC standard entries
        mock_ec1 = Mock()
        mock_ec1.css.return_value.get.side_effect = [
            "EC0217",
            "Impartición de cursos",
            "Desarrollo de Software",  # Comité
            "3"  # Level
        ]
        
        mock_ec2 = Mock()
        mock_ec2.css.return_value.get.side_effect = [
            "EC0435",
            "Prestación de servicios",
            "Servicios TI",
            "2"
        ]
        
        mock_response.css.return_value = [mock_ec1, mock_ec2]
        
        # Execute
        results = list(driver.parse_sector_ec_standards(mock_response))
        
        # Verify
        assert len(results) == 2
        assert all(r["type"] == "ec_sector" for r in results)
        assert results[0]["ec_clave"] == "EC0217"
        assert results[0]["sector_id"] == 1
        assert results[0]["comite_nombre"] == "Desarrollo de Software"
    
    def test_error_handling(self, driver, mock_response):
        """Test error handling in parsing."""
        # Simulate parsing error
        mock_response.css.side_effect = Exception("Parse error")
        
        # Execute - should not raise
        results = list(driver.parse_sector_list(mock_response))
        
        # Verify
        assert len(results) == 0
        assert driver.stats["errors"] == 1
    
    def test_clean_text(self, driver):
        """Test text cleaning utility."""
        assert driver.clean_text("  Text with  spaces  ") == "Text with spaces"
        assert driver.clean_text("Line1\nLine2") == "Line1 Line2"
        assert driver.clean_text("\tTabbed\tText\t") == "Tabbed Text"
        assert driver.clean_text(None) is None
        assert driver.clean_text("") == ""
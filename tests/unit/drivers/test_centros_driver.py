"""
Tests for Centros driver.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from scrapy.http import HtmlResponse, Request

from src.drivers.centros_driver import CentrosDriver


class TestCentrosDriver:
    """Test Centros driver functionality."""
    
    @pytest.fixture
    def driver(self):
        """Create driver instance."""
        driver = CentrosDriver()
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
    
    def test_parse_centro_list(self, driver, mock_response):
        """Test parsing centro list page."""
        # Mock centro rows
        mock_row1 = Mock()
        mock_row1.css.return_value.get.side_effect = [
            "CE0001",  # ID
            "Centro de Evaluación 1",  # Name
            "ECE001-99",  # Certificador
            "Ciudad de México"  # Location
        ]
        
        mock_row2 = Mock()
        mock_row2.css.return_value.get.side_effect = [
            "CE0002",  # ID
            "Centro de Evaluación 2",  # Name
            "OC002-99",  # Certificador
            "Jalisco"  # Location
        ]
        
        mock_response.css.return_value = [mock_row1, mock_row2]
        
        # Execute
        results = list(driver.parse_centro_list(mock_response))
        
        # Verify requests generated
        assert len(results) == 2
        assert all(isinstance(r, Request) for r in results)
        assert "CE0001" in results[0].url
        assert "CE0002" in results[1].url
        assert results[0].meta["centro_id"] == "CE0001"
        assert results[1].meta["centro_id"] == "CE0002"
    
    def test_parse_centro_detail(self, driver, mock_response):
        """Test parsing centro detail page."""
        mock_response.meta = {"centro_id": "CE0001"}
        
        # Mock selectors
        def mock_css_get(selector):
            mapping = {
                "h1::text": "Centro de Evaluación Tecnológica",
                ".cert-id::text": "ECE001-99",
                ".contact-name::text": "María García",
                ".contact-email::text": "contacto@centro.mx",
                ".contact-phone::text": "555-1234-5678",
                ".address::text": "Av. Reforma 200",
                ".municipality::text": "Cuauhtémoc",
                ".state::text": "Ciudad de México",
                ".postal-code::text": "06600"
            }
            return mapping.get(selector)
        
        mock_response.css.return_value.get.side_effect = mock_css_get
        
        # Mock EC standards
        mock_ec_row = Mock()
        mock_ec_row.css.return_value.get.side_effect = ["EC0217", "Impartición de cursos"]
        mock_response.css.return_value.__iter__ = Mock(return_value=iter([mock_ec_row]))
        
        # Execute
        results = list(driver.parse_centro_detail(mock_response))
        
        # Verify centro data
        assert len(results) == 2  # Centro + 1 EC relation
        centro_data = results[0]
        assert centro_data["type"] == "centro"
        assert centro_data["centro_id"] == "CE0001"
        assert centro_data["nombre"] == "Centro de Evaluación Tecnológica"
        assert centro_data["cert_id"] == "ECE001-99"
        assert centro_data["correo"] == "contacto@centro.mx"
        assert centro_data["estado"] == "Ciudad de México"
        
        # Verify EC relation
        ec_relation = results[1]
        assert ec_relation["type"] == "centro_ec"
        assert ec_relation["centro_id"] == "CE0001"
        assert ec_relation["ec_clave"] == "EC0217"
    
    def test_parse_centro_by_cert(self, driver, mock_response):
        """Test parsing centros by certificador page."""
        mock_response.meta = {"cert_id": "ECE001-99"}
        
        # Mock centro entries
        mock_centro1 = Mock()
        mock_centro1.css.return_value.get.side_effect = [
            "CE0001",
            "Centro 1",
            "Ciudad de México",
            "Benito Juárez"
        ]
        
        mock_centro2 = Mock()
        mock_centro2.css.return_value.get.side_effect = [
            "CE0002",
            "Centro 2",
            "Jalisco",
            "Guadalajara"
        ]
        
        mock_response.css.return_value = [mock_centro1, mock_centro2]
        
        # Execute
        results = list(driver.parse_centro_by_cert(mock_response))
        
        # Verify
        assert len(results) == 2
        assert all(r["type"] == "centro" for r in results)
        assert results[0]["centro_id"] == "CE0001"
        assert results[0]["cert_id"] == "ECE001-99"
        assert results[1]["centro_id"] == "CE0002"
        assert results[1]["cert_id"] == "ECE001-99"
    
    def test_normalize_state_name(self, driver):
        """Test state name normalization."""
        assert driver.normalize_state_name("CDMX") == "Ciudad de México"
        assert driver.normalize_state_name("cdmx") == "Ciudad de México"
        assert driver.normalize_state_name("Ciudad de México") == "Ciudad de México"
        assert driver.normalize_state_name("mexico") == "Estado de México"
        assert driver.normalize_state_name("NL") == "Nuevo León"
        assert driver.normalize_state_name("Jalisco") == "Jalisco"
        assert driver.normalize_state_name("Unknown") == "Unknown"
    
    def test_get_estado_inegi(self, driver):
        """Test INEGI state code mapping."""
        assert driver.get_estado_inegi("Ciudad de México") == "09"
        assert driver.get_estado_inegi("Jalisco") == "14"
        assert driver.get_estado_inegi("Nuevo León") == "19"
        assert driver.get_estado_inegi("Unknown") is None
    
    def test_parse_latlong(self, driver):
        """Test latitude/longitude parsing."""
        lat, lon = driver.parse_latlong("19.4326,-99.1332")
        assert lat == 19.4326
        assert lon == -99.1332
        
        lat, lon = driver.parse_latlong("19.4326, -99.1332")
        assert lat == 19.4326
        assert lon == -99.1332
        
        lat, lon = driver.parse_latlong("invalid")
        assert lat is None
        assert lon is None
    
    def test_parse_centro_standards(self, driver, mock_response):
        """Test parsing centro EC standards page."""
        mock_response.meta = {"centro_id": "CE0001"}
        
        # Mock EC standard rows
        mock_ec1 = Mock()
        mock_ec1.css.return_value.get.side_effect = [
            "EC0217",
            "Impartición de cursos",
            "2020-01-15"  # Registration date
        ]
        
        mock_ec2 = Mock()
        mock_ec2.css.return_value.get.side_effect = [
            "EC0435",
            "Prestación de servicios",
            "2021-06-01"
        ]
        
        mock_response.css.return_value = [mock_ec1, mock_ec2]
        
        # Execute
        results = list(driver.parse_centro_standards(mock_response))
        
        # Verify
        assert len(results) == 2
        assert all(r["type"] == "centro_ec" for r in results)
        assert results[0]["centro_id"] == "CE0001"
        assert results[0]["ec_clave"] == "EC0217"
        assert results[0]["fecha_registro"] == "2020-01-15"
        assert results[1]["ec_clave"] == "EC0435"
    
    def test_error_handling(self, driver, mock_response):
        """Test error handling in parsing."""
        # Simulate parsing error
        mock_response.css.side_effect = Exception("Parse error")
        
        # Execute - should not raise
        results = list(driver.parse_centro_list(mock_response))
        
        # Verify
        assert len(results) == 0
        assert driver.stats["errors"] == 1
    
    def test_extract_contact_info(self, driver):
        """Test contact info extraction."""
        # Test email extraction
        assert driver.extract_contact_info("Email: test@example.com", "email") == "test@example.com"
        assert driver.extract_contact_info("correo: TEST@EXAMPLE.COM", "email") == "test@example.com"
        
        # Test phone extraction
        assert driver.extract_contact_info("Tel: 555-1234-5678", "phone") == "555-1234-5678"
        assert driver.extract_contact_info("Teléfono: (555) 1234 5678", "phone") == "5551234567"
        
        # Test invalid
        assert driver.extract_contact_info("No info", "email") is None
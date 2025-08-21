"""Unit tests for RENEC spider."""

import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import Request, Response, TextResponse

from src.discovery.spiders.renec_spider import RenecSpider
from src.discovery.items import CrawlMapItem, RenecItem


class TestRenecSpider:
    """Test cases for RenecSpider."""
    
    def test_spider_initialization(self):
        """Test spider initialization with different modes."""
        # Test crawl mode
        spider = RenecSpider(mode="crawl", max_depth=3)
        assert spider.mode == "crawl"
        assert spider.max_depth == 3
        assert len(spider.visited_urls) == 0
        
        # Test harvest mode
        spider = RenecSpider(mode="harvest")
        assert spider.mode == "harvest"
        assert spider.max_depth == 5  # default
    
    def test_start_requests_crawl_mode(self):
        """Test start requests generation in crawl mode."""
        spider = RenecSpider(mode="crawl")
        requests = list(spider.start_requests())
        
        assert len(requests) == 1
        assert requests[0].url == "https://conocer.gob.mx"
        assert requests[0].meta["depth"] == 0
        assert requests[0].meta["playwright"] is True
    
    def test_start_requests_harvest_mode(self):
        """Test start requests generation in harvest mode."""
        spider = RenecSpider(mode="harvest")
        requests = list(spider.start_requests())
        
        assert len(requests) > 0
        # Check that requests are for known endpoints
        urls = [req.url for req in requests]
        assert any("estandares" in url for url in urls)
        assert any("certificador" in url or "oec" in url for url in urls)
    
    def test_detect_component_type(self):
        """Test component type detection."""
        spider = RenecSpider()
        
        # Create mock responses
        ec_response = MagicMock(url="https://conocer.gob.mx/estandares-de-competencia/ec0001")
        ec_response.text = "Estándar de Competencia EC0001"
        
        cert_response = MagicMock(url="https://conocer.gob.mx/organismos-certificadores/oc001")
        cert_response.text = "Entidad de Certificación OC001"
        
        center_response = MagicMock(url="https://conocer.gob.mx/centros-evaluacion/ce001")
        center_response.text = "Centro de Evaluación CE001"
        
        # Test detection
        assert spider._detect_component_type(ec_response) == "ec_standard"
        assert spider._detect_component_type(cert_response) == "certificador"
        assert spider._detect_component_type(center_response) == "center"
    
    def test_should_follow_url(self):
        """Test URL filtering logic."""
        spider = RenecSpider()
        spider.allowed_domains = ["conocer.gob.mx"]
        
        # Should follow
        assert spider._should_follow_url("https://conocer.gob.mx/page")
        assert spider._should_follow_url("https://conocer.gob.mx/ec/123")
        
        # Should not follow
        assert not spider._should_follow_url("https://external.com/page")
        assert not spider._should_follow_url("https://conocer.gob.mx/file.pdf")
        assert not spider._should_follow_url("https://conocer.gob.mx/image.jpg")
        
        # Already visited
        spider.visited_urls.add("https://conocer.gob.mx/visited")
        assert not spider._should_follow_url("https://conocer.gob.mx/visited")
    
    @pytest.mark.asyncio
    async def test_parse_crawl(self):
        """Test crawl parsing."""
        spider = RenecSpider(mode="crawl", max_depth=2)
        
        # Create mock response
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <a href="/page1">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="https://external.com">External</a>
            </body>
        </html>
        """
        
        response = TextResponse(
            url="https://conocer.gob.mx/test",
            body=html.encode("utf-8"),
            encoding="utf-8",
        )
        response.meta = {"depth": 0, "parent_url": None}
        
        # Parse response
        items = []
        requests = []
        
        async for result in spider.parse_crawl(response):
            if isinstance(result, CrawlMapItem):
                items.append(result)
            elif isinstance(result, Request):
                requests.append(result)
        
        # Check results
        assert len(items) == 1
        assert items[0]["url"] == "https://conocer.gob.mx/test"
        assert items[0]["title"] == "Test Page"
        assert items[0]["depth"] == 0
        
        # Should generate 2 requests (internal links only)
        assert len(requests) == 2
        assert all(req.meta["depth"] == 1 for req in requests)
    
    def test_extract_ec_standards(self):
        """Test EC standard extraction."""
        spider = RenecSpider()
        
        # Create mock response with EC standard data
        html = """
        <div class="estandar-item">
            <span class="ec-code">EC0001</span>
            <h3 class="ec-title">Competencia en desarrollo</h3>
            <span class="sector">Tecnología</span>
            <span class="nivel">Nivel 3</span>
            <span class="fecha">2023-01-15</span>
        </div>
        """
        
        response = TextResponse(
            url="https://conocer.gob.mx/estandares",
            body=html.encode("utf-8"),
            encoding="utf-8",
        )
        
        # Extract items
        items = list(spider._extract_ec_standards(response))
        
        assert len(items) == 1
        assert items[0]["type"] == "ec_standard"
        assert items[0]["code"] == "EC0001"
        assert items[0]["title"] == "Competencia en desarrollo"
        assert items[0]["sector"] == "Tecnología"
    
    def test_extract_certificadores(self):
        """Test certificador extraction."""
        spider = RenecSpider()
        
        html = """
        <div class="oec-item">
            <h3 class="oec-name">Centro Certificador</h3>
            <span class="oec-code">OC001</span>
            <a href="mailto:contacto@cert.mx">contacto@cert.mx</a>
            <span class="telefono">555-1234</span>
            <div class="direccion">Av. Principal 123</div>
        </div>
        """
        
        response = TextResponse(
            url="https://conocer.gob.mx/certificadores",
            body=html.encode("utf-8"),
            encoding="utf-8",
        )
        
        items = list(spider._extract_certificadores(response))
        
        assert len(items) == 1
        assert items[0]["type"] == "certificador"
        assert items[0]["name"] == "Centro Certificador"
        assert items[0]["code"] == "OC001"
        assert items[0]["contact_email"] == "contacto@cert.mx"


class TestSpiderIntegration:
    """Integration tests for spider functionality."""
    
    @patch("scrapy.Spider.logger")
    def test_spider_closed_callback(self, mock_logger):
        """Test spider closed callback."""
        spider = RenecSpider()
        spider.visited_urls = {"url1", "url2", "url3"}
        spider.network_requests = [{"url": "api1"}, {"url": "api2"}]
        
        spider.closed("finished")
        
        # Check that logger was called
        assert mock_logger.info.called
        
    def test_network_request_recording(self):
        """Test network request recording structure."""
        spider = RenecSpider()
        
        # Simulate network request
        request_data = {
            "url": "https://conocer.gob.mx/api/v1/standards",
            "method": "GET",
            "headers": {"Accept": "application/json"},
            "timestamp": "2023-01-01T00:00:00",
        }
        
        spider.network_requests.append(request_data)
        
        assert len(spider.network_requests) == 1
        assert spider.network_requests[0]["url"] == request_data["url"]
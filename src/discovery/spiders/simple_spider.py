"""Simple spider for local testing without Playwright dependencies."""

import scrapy
from scrapy.http import Request, Response
from urllib.parse import urljoin, urlparse
import logging

from src.discovery.items import CrawlMapItem


class SimpleSpider(scrapy.Spider):
    """Simple spider for basic functionality testing."""
    
    name = "simple"
    allowed_domains = ["httpbin.org", "conocer.gob.mx"]
    
    # Start with safe test URLs
    start_urls = [
        "http://httpbin.org/html",
        "http://httpbin.org/json",
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, test_conocer=False, *args, **kwargs):
        """Initialize spider with optional CONOCER testing."""
        super().__init__(*args, **kwargs)
        self.test_conocer = test_conocer
        
        if self.test_conocer:
            # Add CONOCER URLs for testing
            self.start_urls.extend([
                "https://conocer.gob.mx/",
                "https://conocer.gob.mx/portal-conocer/",
            ])
            self.logger.info("CONOCER testing enabled - will attempt SSL bypass")

    def start_requests(self):
        """Generate initial requests with proper headers."""
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                headers={
                    'User-Agent': 'RENEC-Harvester/0.2.0 Local-Testing',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
                },
                meta={
                    'dont_filter': True,
                    'download_timeout': 30,
                }
            )

    def parse(self, response):
        """Parse response and extract basic information."""
        self.logger.info(f"Successfully parsed {response.url} - Status: {response.status}")
        
        # Create basic crawl item
        item = CrawlMapItem()
        item['url'] = response.url
        item['title'] = self._extract_title(response)
        item['type'] = self._detect_page_type(response)
        item['status_code'] = response.status
        item['content_hash'] = self._generate_content_hash(response.body)
        
        yield item
        
        # If testing CONOCER, try to find RENEC-related links
        if self.test_conocer and 'conocer.gob.mx' in response.url:
            self._extract_renec_links(response)

    def _extract_title(self, response):
        """Extract page title."""
        # Handle JSON responses
        if 'application/json' in response.headers.get('content-type', b'').decode():
            return "JSON Response"
        
        try:
            title = response.css('title::text').get()
            if not title:
                title = response.css('h1::text').get()
            if not title:
                title = "No title found"
            return title.strip()
        except ValueError:
            # Handle non-HTML content
            return f"Non-HTML content ({response.headers.get('content-type', b'unknown').decode()})"

    def _detect_page_type(self, response):
        """Detect page type based on URL and content."""
        url = response.url.lower()
        content = response.text.lower()
        
        if 'httpbin.org' in url:
            return 'test_page'
        elif 'conocer.gob.mx' in url:
            if any(term in content for term in ['renec', 'estándar', 'competencia']):
                return 'renec_related'
            elif any(term in content for term in ['certificador', 'oec', 'organismo']):
                return 'certificador_related'
            else:
                return 'conocer_general'
        else:
            return 'unknown'

    def _generate_content_hash(self, content):
        """Generate simple content hash."""
        import hashlib
        return hashlib.md5(content).hexdigest()[:16]

    def _extract_renec_links(self, response):
        """Extract potential RENEC-related links."""
        links = response.css('a::attr(href)').getall()
        renec_links = []
        
        for link in links:
            if not link:
                continue
                
            # Convert to absolute URL
            absolute_url = urljoin(response.url, link)
            
            # Check if link might be RENEC-related
            if any(term in link.lower() for term in ['renec', 'competencia', 'estandar', 'certificador']):
                renec_links.append(absolute_url)
        
        if renec_links:
            self.logger.info(f"Found {len(renec_links)} potential RENEC links:")
            for link in renec_links[:10]:  # Log first 10
                self.logger.info(f"  - {link}")
        
        return renec_links

    def parse_error(self, failure):
        """Handle parsing errors."""
        self.logger.error(f"Error parsing {failure.request.url}: {failure.value}")
        
        # Still yield an item with error information
        item = CrawlMapItem()
        item['url'] = failure.request.url
        item['title'] = 'ERROR'
        item['type'] = 'error'
        item['status_code'] = getattr(failure.value, 'response', {}).get('status', 0) if hasattr(failure.value, 'response') else 0
        item['content_hash'] = 'error'
        
        yield item
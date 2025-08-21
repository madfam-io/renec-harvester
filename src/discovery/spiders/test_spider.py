"""Simple test spider for basic functionality."""

import scrapy
from scrapy.http import Request, Response

from src.discovery.items import CrawlMapItem


class TestSpider(scrapy.Spider):
    """Simple test spider."""
    
    name = "test"
    allowed_domains = ["httpbin.org"]
    start_urls = ["http://httpbin.org/html"]

    def parse(self, response):
        """Parse test response."""
        self.logger.info(f"Parsing {response.url}")
        
        # Create simple item
        item = CrawlMapItem()
        item["url"] = response.url
        item["title"] = response.css("title::text").get("Test Page")
        item["type"] = "test"
        item["depth"] = 0
        item["status_code"] = response.status
        
        yield item
        
        self.logger.info("Test spider completed successfully!")
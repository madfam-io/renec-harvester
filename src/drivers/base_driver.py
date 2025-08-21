"""
Base driver class for RENEC data extraction.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Generator
import logging
from datetime import datetime
import hashlib
import json

from scrapy.http import Response
from scrapy import Request

logger = logging.getLogger(__name__)


class BaseDriver(ABC):
    """Base class for all RENEC component drivers."""
    
    def __init__(self, spider):
        """
        Initialize driver with spider reference.
        
        Args:
            spider: The Scrapy spider instance
        """
        self.spider = spider
        self.stats = {
            'items_extracted': 0,
            'pages_processed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    @abstractmethod
    def get_start_urls(self) -> List[str]:
        """
        Get initial URLs for this driver.
        
        Returns:
            List of starting URLs
        """
        pass
    
    @abstractmethod
    def parse(self, response: Response) -> Generator[Any, None, None]:
        """
        Parse response and yield items or requests.
        
        Args:
            response: Scrapy Response object
            
        Yields:
            Dict items or Request objects
        """
        pass
    
    @abstractmethod
    def parse_detail(self, response: Response) -> Dict[str, Any]:
        """
        Parse detail page for complete item data.
        
        Args:
            response: Scrapy Response object from detail page
            
        Returns:
            Complete item dictionary
        """
        pass
    
    def compute_content_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute hash of item content for change detection.
        
        Args:
            data: Item dictionary
            
        Returns:
            SHA256 hash string
        """
        # Sort keys for consistent hashing
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def extract_text(self, selector, xpath: str, default: str = '') -> str:
        """
        Safely extract text from selector.
        
        Args:
            selector: Scrapy Selector
            xpath: XPath expression
            default: Default value if not found
            
        Returns:
            Extracted text or default
        """
        try:
            text = selector.xpath(xpath).get()
            return (text or default).strip()
        except Exception as e:
            logger.warning(f"Failed to extract text from {xpath}: {e}")
            return default
    
    def extract_all_text(self, selector, xpath: str) -> List[str]:
        """
        Extract all matching text from selector.
        
        Args:
            selector: Scrapy Selector
            xpath: XPath expression
            
        Returns:
            List of extracted text
        """
        try:
            return [t.strip() for t in selector.xpath(xpath).getall() if t.strip()]
        except Exception as e:
            logger.warning(f"Failed to extract all text from {xpath}: {e}")
            return []
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.replace('\xa0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')  # Zero-width space
        
        return text.strip()
    
    def build_absolute_url(self, response: Response, relative_url: str) -> str:
        """
        Build absolute URL from relative path.
        
        Args:
            response: Current response object
            relative_url: Relative URL path
            
        Returns:
            Absolute URL
        """
        return response.urljoin(relative_url)
    
    def create_request(self, 
                      url: str, 
                      callback,
                      meta: Optional[Dict] = None,
                      priority: int = 0) -> Request:
        """
        Create a Scrapy Request with driver metadata.
        
        Args:
            url: Target URL
            callback: Callback method
            meta: Additional metadata
            priority: Request priority
            
        Returns:
            Configured Request object
        """
        request_meta = {
            'driver': self.__class__.__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        if meta:
            request_meta.update(meta)
        
        return Request(
            url=url,
            callback=callback,
            meta=request_meta,
            priority=priority,
            dont_filter=False
        )
    
    def handle_pagination(self, response: Response) -> Optional[Request]:
        """
        Handle pagination if present.
        
        Args:
            response: Current page response
            
        Returns:
            Request for next page or None
        """
        # Look for common pagination patterns
        next_page_selectors = [
            '//a[contains(@class, "siguiente")]/@href',
            '//a[contains(text(), "Siguiente")]/@href',
            '//a[contains(@class, "next")]/@href',
            '//a[@rel="next"]/@href',
            '//li[@class="pagination-next"]/a/@href'
        ]
        
        for selector in next_page_selectors:
            next_url = response.xpath(selector).get()
            if next_url:
                return self.create_request(
                    url=self.build_absolute_url(response, next_url),
                    callback=self.parse,
                    priority=1
                )
        
        return None
    
    def update_stats(self, stat_type: str, increment: int = 1):
        """
        Update driver statistics.
        
        Args:
            stat_type: Type of statistic to update
            increment: Amount to increment
        """
        if stat_type in self.stats:
            self.stats[stat_type] += increment
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Get summary of driver statistics.
        
        Returns:
            Statistics dictionary
        """
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'runtime_seconds': runtime,
            'items_per_second': self.stats['items_extracted'] / runtime if runtime > 0 else 0
        }
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate extracted item meets requirements.
        
        Args:
            item: Item dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Override in subclasses for specific validation
        return True
    
    def log_extraction_error(self, response: Response, error: Exception):
        """
        Log extraction error with context.
        
        Args:
            response: Response that caused error
            error: Exception that occurred
        """
        logger.error(
            f"Extraction error in {self.__class__.__name__} "
            f"for URL {response.url}: {error}",
            extra={
                'driver': self.__class__.__name__,
                'url': response.url,
                'status': response.status,
                'error_type': type(error).__name__
            }
        )
        self.update_stats('errors')
"""Main RENEC spider with parallel crawling capabilities."""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Generator, Optional
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import Request, Response
from scrapy_playwright.page import PageMethod
from structlog import get_logger

from src.core.constants import (
    COMPONENT_TYPES,
    RENEC_BASE_URL,
    RENEC_ENDPOINTS,
    XPATH_SELECTORS,
)
from src.discovery.items import CrawlMapItem, RenecItem

logger = get_logger()


class RenecSpider(scrapy.Spider):
    """Enhanced RENEC spider with Playwright integration and parallel processing."""
    
    name = "renec"
    allowed_domains = ["conocer.gob.mx"]
    custom_settings = {
        "CONCURRENT_REQUESTS": 10,
        "DOWNLOAD_DELAY": 0.5,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    }

    def __init__(self, mode: str = "crawl", max_depth: int = 5, *args, **kwargs):
        """Initialize spider with mode and depth configuration.
        
        Args:
            mode: Operation mode - 'crawl' for mapping, 'harvest' for extraction
            max_depth: Maximum crawl depth
        """
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.max_depth = max_depth
        self.visited_urls = set()
        self.network_requests = []
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        logger.info(
            "Spider initialized",
            mode=self.mode,
            max_depth=self.max_depth,
            session_id=self.session_id,
        )

    def start_requests(self) -> Generator[Request, None, None]:
        """Generate initial requests based on mode."""
        if self.mode == "crawl":
            # Start from main page for IR-rooted crawl
            yield Request(
                RENEC_BASE_URL,
                callback=self.parse_crawl,
                meta={
                    "depth": 0,
                    "parent_url": None,
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_timeout", 1000),
                    ],
                },
            )
        else:
            # Start from known endpoints for harvest mode
            for endpoint_type, endpoints in RENEC_ENDPOINTS.items():
                for endpoint in endpoints:
                    url = urljoin(RENEC_BASE_URL, endpoint)
                    yield Request(
                        url,
                        callback=self.parse_harvest,
                        meta={
                            "component_type": endpoint_type,
                            "playwright": True,
                            "playwright_include_page": True,
                            "playwright_page_methods": [
                                PageMethod("wait_for_load_state", "networkidle"),
                            ],
                        },
                    )

    async def parse_crawl(self, response: Response) -> Generator[Any, None, None]:
        """Parse page in crawl mode to build site map."""
        page = response.meta.get("playwright_page")
        current_depth = response.meta.get("depth", 0)
        parent_url = response.meta.get("parent_url")
        
        # Record network activity
        if page:
            await self._record_network_activity(page)
            
        # Extract page information
        url_hash = hashlib.md5(response.url.encode()).hexdigest()
        
        if response.url not in self.visited_urls:
            self.visited_urls.add(response.url)
            
            # Create crawl map item
            item = CrawlMapItem(
                url=response.url,
                url_hash=url_hash,
                title=response.css("title::text").get(""),
                type=self._detect_component_type(response),
                parent_url=parent_url,
                depth=current_depth,
                timestamp=datetime.utcnow().isoformat(),
                status_code=response.status,
                content_hash=hashlib.md5(response.body).hexdigest(),
            )
            
            yield item
            
            # Extract links if within depth limit
            if current_depth < self.max_depth:
                links = response.css("a::attr(href)").getall()
                for link in links:
                    absolute_url = urljoin(response.url, link)
                    
                    # Filter URLs
                    if self._should_follow_url(absolute_url):
                        yield Request(
                            absolute_url,
                            callback=self.parse_crawl,
                            meta={
                                "depth": current_depth + 1,
                                "parent_url": response.url,
                                "playwright": True,
                                "playwright_include_page": True,
                                "playwright_page_methods": [
                                    PageMethod("wait_for_load_state", "networkidle"),
                                ],
                            },
                            dont_filter=False,
                        )
        
        # Close page to free resources
        if page:
            await page.close()

    async def parse_harvest(self, response: Response) -> Generator[Any, None, None]:
        """Parse page in harvest mode to extract component data."""
        page = response.meta.get("playwright_page")
        component_type = response.meta.get("component_type")
        
        logger.info(
            "Harvesting component",
            url=response.url,
            component_type=component_type,
        )
        
        # Wait for dynamic content
        if page:
            try:
                # Wait for specific selectors based on component type
                selectors = XPATH_SELECTORS.get(component_type, {})
                if selectors:
                    await page.wait_for_selector(
                        list(selectors.values())[0],
                        timeout=10000,
                    )
            except Exception as e:
                logger.warning(
                    "Selector wait timeout",
                    url=response.url,
                    error=str(e),
                )
        
        # Extract data based on component type
        if component_type == "ec_standard":
            yield from self._extract_ec_standards(response)
        elif component_type == "certificador":
            yield from self._extract_certificadores(response)
        elif component_type == "center":
            yield from self._extract_centers(response)
        elif component_type == "course":
            yield from self._extract_courses(response)
        
        # Handle pagination
        next_page = response.css(".pagination .next a::attr(href)").get()
        if next_page:
            yield Request(
                urljoin(response.url, next_page),
                callback=self.parse_harvest,
                meta={
                    "component_type": component_type,
                    "playwright": True,
                    "playwright_include_page": True,
                },
            )
        
        # Close page
        if page:
            await page.close()

    def _detect_component_type(self, response: Response) -> str:
        """Detect component type from URL and content."""
        url = response.url.lower()
        
        # URL-based detection
        for component_type, patterns in COMPONENT_TYPES.items():
            for pattern in patterns:
                if pattern in url:
                    return component_type
        
        # Content-based detection
        if "estándar de competencia" in response.text.lower():
            return "ec_standard"
        elif "entidad de certificación" in response.text.lower():
            return "certificador"
        elif "centro de evaluación" in response.text.lower():
            return "center"
        
        return "general"

    def _should_follow_url(self, url: str) -> bool:
        """Determine if URL should be followed."""
        parsed = urlparse(url)
        
        # Check domain
        if parsed.netloc not in self.allowed_domains:
            return False
        
        # Skip non-HTML resources
        skip_extensions = {".pdf", ".jpg", ".png", ".gif", ".doc", ".docx", ".xls", ".xlsx"}
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip already visited
        if url in self.visited_urls:
            return False
        
        return True

    async def _record_network_activity(self, page) -> None:
        """Record network requests for API discovery."""
        try:
            # Set up network event listeners
            async def on_request(request):
                if request.resource_type in ["xhr", "fetch"]:
                    self.network_requests.append({
                        "url": request.url,
                        "method": request.method,
                        "headers": dict(request.headers),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            
            page.on("request", on_request)
            
            # Wait for network activity
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            logger.error("Network recording error", error=str(e))

    def _extract_ec_standards(self, response: Response) -> Generator[RenecItem, None, None]:
        """Extract EC standards from response."""
        selectors = XPATH_SELECTORS.get("ec_standard", {})
        
        # Extract standard items
        for item in response.xpath(selectors.get("container", "//div")):
            yield RenecItem(
                type="ec_standard",
                code=item.xpath(selectors.get("code", ".//text()")).get(),
                title=item.xpath(selectors.get("title", ".//text()")).get(),
                sector=item.xpath(selectors.get("sector", ".//text()")).get(),
                level=item.xpath(selectors.get("level", ".//text()")).get(),
                publication_date=item.xpath(selectors.get("publication_date", ".//text()")).get(),
                url=response.url,
                extracted_at=datetime.utcnow().isoformat(),
            )

    def _extract_certificadores(self, response: Response) -> Generator[RenecItem, None, None]:
        """Extract certificadores from response."""
        selectors = XPATH_SELECTORS.get("certificador", {})
        
        for item in response.xpath(selectors.get("container", "//div")):
            yield RenecItem(
                type="certificador",
                name=item.xpath(selectors.get("name", ".//text()")).get(),
                code=item.xpath(selectors.get("code", ".//text()")).get(),
                contact_email=item.xpath(selectors.get("email", ".//text()")).get(),
                contact_phone=item.xpath(selectors.get("phone", ".//text()")).get(),
                address=item.xpath(selectors.get("address", ".//text()")).get(),
                url=response.url,
                extracted_at=datetime.utcnow().isoformat(),
            )

    def _extract_centers(self, response: Response) -> Generator[RenecItem, None, None]:
        """Extract evaluation centers from response."""
        selectors = XPATH_SELECTORS.get("center", {})
        
        for item in response.xpath(selectors.get("container", "//div")):
            yield RenecItem(
                type="center",
                name=item.xpath(selectors.get("name", ".//text()")).get(),
                code=item.xpath(selectors.get("code", ".//text()")).get(),
                certificador_code=item.xpath(selectors.get("certificador", ".//text()")).get(),
                contact_email=item.xpath(selectors.get("email", ".//text()")).get(),
                contact_phone=item.xpath(selectors.get("phone", ".//text()")).get(),
                address=item.xpath(selectors.get("address", ".//text()")).get(),
                url=response.url,
                extracted_at=datetime.utcnow().isoformat(),
            )

    def _extract_courses(self, response: Response) -> Generator[RenecItem, None, None]:
        """Extract courses from response."""
        selectors = XPATH_SELECTORS.get("course", {})
        
        for item in response.xpath(selectors.get("container", "//div")):
            yield RenecItem(
                type="course",
                name=item.xpath(selectors.get("name", ".//text()")).get(),
                ec_code=item.xpath(selectors.get("ec_code", ".//text()")).get(),
                duration=item.xpath(selectors.get("duration", ".//text()")).get(),
                modality=item.xpath(selectors.get("modality", ".//text()")).get(),
                url=response.url,
                extracted_at=datetime.utcnow().isoformat(),
            )

    def closed(self, reason: str) -> None:
        """Spider closed callback."""
        logger.info(
            "Spider closed",
            reason=reason,
            session_id=self.session_id,
            urls_visited=len(self.visited_urls),
            network_requests=len(self.network_requests),
        )
        
        # Save network requests
        if self.network_requests:
            output_file = f"artifacts/network_requests_{self.session_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.network_requests, f, indent=2, ensure_ascii=False)
            logger.info("Network requests saved", file=output_file)
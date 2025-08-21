"""Scrapy items for RENEC harvester."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import scrapy
from scrapy.item import Field


class CrawlMapItem(scrapy.Item):
    """Item for site crawl mapping."""
    
    url = Field()
    url_hash = Field()
    title = Field()
    type = Field()
    parent_url = Field()
    depth = Field()
    timestamp = Field()
    status_code = Field()
    content_hash = Field()
    headers = Field()
    meta_tags = Field()


class RenecItem(scrapy.Item):
    """Generic item for RENEC components."""
    
    # Common fields
    type = Field()  # ec_standard, certificador, center, course
    url = Field()
    extracted_at = Field()
    
    # EC Standard fields
    code = Field()
    title = Field()
    sector = Field()
    level = Field()
    publication_date = Field()
    expiration_date = Field()
    status = Field()
    
    # Organization fields (certificador/center)
    name = Field()
    rfc = Field()
    contact_email = Field()
    contact_phone = Field()
    contact_name = Field()
    address = Field()
    city = Field()
    state = Field()
    postal_code = Field()
    
    # Relationship fields
    certificador_code = Field()
    ec_codes = Field()
    center_codes = Field()
    
    # Course fields
    ec_code = Field()
    duration = Field()
    modality = Field()
    price = Field()
    start_date = Field()
    end_date = Field()
    
    # Metadata
    first_seen = Field()
    last_seen = Field()
    content_hash = Field()
    changes = Field()


@dataclass
class NetworkRequest:
    """Network request captured during crawling."""
    
    url: str
    method: str
    headers: Dict[str, str]
    timestamp: datetime
    resource_type: str
    status_code: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_size: Optional[int] = None
    duration_ms: Optional[float] = None


@dataclass
class ExtractedData:
    """Normalized extracted data."""
    
    component_type: str
    data: Dict[str, any]
    relationships: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)
    validation_errors: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if data passed validation."""
        return len(self.validation_errors) == 0
    
    def add_relationship(self, rel_type: str, target_type: str, target_id: str) -> None:
        """Add a relationship to another component."""
        self.relationships.append({
            "type": rel_type,
            "target_type": target_type,
            "target_id": target_id,
            "added_at": datetime.utcnow().isoformat(),
        })
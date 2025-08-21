"""Scrapy pipelines for data processing and storage."""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Optional

import phonenumbers
import redis
from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from structlog import get_logger

from src.core.constants import VALIDATION_PATTERNS
from src.models import get_session
from src.models.components import ECStandard, Certificador, EvaluationCenter, Course
from src.models.crawl import CrawlMap, NetworkCapture
from src.monitoring.metrics import harvest_metrics

logger = get_logger()


class ValidationPipeline:
    """Validate extracted items against defined patterns."""
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Validate item fields."""
        item_type = item.get("type")
        
        if not item_type:
            raise DropItem("Missing item type")
        
        # Track validation start
        validation_errors = []
        
        # Validate based on item type
        if item_type == "ec_standard":
            validation_errors.extend(self._validate_ec_standard(item))
        elif item_type == "certificador":
            validation_errors.extend(self._validate_certificador(item))
        elif item_type == "center":
            validation_errors.extend(self._validate_center(item))
        elif item_type == "course":
            validation_errors.extend(self._validate_course(item))
        
        # Check for validation errors
        if validation_errors:
            for error in validation_errors:
                harvest_metrics["validation_failures"].labels(
                    component_type=item_type,
                    field=error["field"],
                ).inc()
            
            logger.warning(
                "Validation errors found",
                item_type=item_type,
                errors=validation_errors,
                url=item.get("url"),
            )
            
            # Add errors to item for potential recovery
            item["validation_errors"] = validation_errors
        
        return item
    
    def _validate_ec_standard(self, item: Dict[str, Any]) -> list:
        """Validate EC standard fields."""
        errors = []
        
        # Validate code
        code = item.get("code")
        if not code:
            errors.append({"field": "code", "error": "Missing EC code"})
        elif not re.match(VALIDATION_PATTERNS["ec_code"], code):
            errors.append({"field": "code", "error": f"Invalid EC code format: {code}"})
        
        # Validate title
        if not item.get("title"):
            errors.append({"field": "title", "error": "Missing EC title"})
        
        # Validate level
        level = item.get("level")
        if level and not isinstance(level, int):
            try:
                item["level"] = int(level)
            except (ValueError, TypeError):
                errors.append({"field": "level", "error": f"Invalid level: {level}"})
        
        return errors
    
    def _validate_certificador(self, item: Dict[str, Any]) -> list:
        """Validate certificador fields."""
        errors = []
        
        # Validate code
        code = item.get("code")
        if code and not re.match(VALIDATION_PATTERNS["oec_code"], code):
            errors.append({"field": "code", "error": f"Invalid OEC code format: {code}"})
        
        # Validate name
        if not item.get("name"):
            errors.append({"field": "name", "error": "Missing certificador name"})
        
        # Validate email
        email = item.get("contact_email")
        if email and not re.match(VALIDATION_PATTERNS["email"], email):
            errors.append({"field": "contact_email", "error": f"Invalid email: {email}"})
        
        # Validate RFC
        rfc = item.get("rfc")
        if rfc and not re.match(VALIDATION_PATTERNS["rfc"], rfc):
            errors.append({"field": "rfc", "error": f"Invalid RFC: {rfc}"})
        
        return errors
    
    def _validate_center(self, item: Dict[str, Any]) -> list:
        """Validate evaluation center fields."""
        errors = []
        
        # Validate code
        code = item.get("code")
        if code and not re.match(VALIDATION_PATTERNS["ce_code"], code):
            errors.append({"field": "code", "error": f"Invalid CE code format: {code}"})
        
        # Validate name
        if not item.get("name"):
            errors.append({"field": "name", "error": "Missing center name"})
        
        # Validate certificador relationship
        if not item.get("certificador_code"):
            errors.append({"field": "certificador_code", "error": "Missing certificador code"})
        
        return errors
    
    def _validate_course(self, item: Dict[str, Any]) -> list:
        """Validate course fields."""
        errors = []
        
        # Validate name
        if not item.get("name"):
            errors.append({"field": "name", "error": "Missing course name"})
        
        # Validate EC code relationship
        ec_code = item.get("ec_code")
        if ec_code and not re.match(VALIDATION_PATTERNS["ec_code"], ec_code):
            errors.append({"field": "ec_code", "error": f"Invalid EC code: {ec_code}"})
        
        # Validate duration
        duration = item.get("duration")
        if duration and not isinstance(duration, (int, float)):
            try:
                item["duration_hours"] = int(re.search(r"\d+", str(duration)).group())
            except (AttributeError, ValueError):
                errors.append({"field": "duration", "error": f"Invalid duration: {duration}"})
        
        return errors


class NormalizationPipeline:
    """Normalize and clean extracted data."""
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Normalize item fields."""
        item_type = item.get("type")
        
        # Common normalization
        item = self._normalize_common_fields(item)
        
        # Type-specific normalization
        if item_type == "ec_standard":
            item = self._normalize_ec_standard(item)
        elif item_type in ["certificador", "center"]:
            item = self._normalize_organization(item)
        elif item_type == "course":
            item = self._normalize_course(item)
        
        # Add metadata
        item["content_hash"] = self._calculate_content_hash(item)
        item["normalized_at"] = datetime.utcnow().isoformat()
        
        return item
    
    def _normalize_common_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize common fields across all item types."""
        # Trim whitespace
        for field in ["title", "name", "address", "city", "state"]:
            if field in item and item[field]:
                item[field] = item[field].strip()
        
        # Normalize phone numbers
        if "contact_phone" in item and item["contact_phone"]:
            item["contact_phone"] = self._normalize_phone(item["contact_phone"])
        
        # Normalize emails
        if "contact_email" in item and item["contact_email"]:
            item["contact_email"] = item["contact_email"].lower().strip()
        
        # Normalize URLs
        if "url" in item and item["url"]:
            item["url"] = item["url"].strip().rstrip("/")
        
        return item
    
    def _normalize_ec_standard(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize EC standard fields."""
        # Normalize code
        if "code" in item:
            item["code"] = item["code"].upper().strip()
        
        # Parse dates
        for date_field in ["publication_date", "expiration_date"]:
            if date_field in item and item[date_field]:
                item[date_field] = self._parse_date(item[date_field])
        
        # Normalize sector
        if "sector" in item and item["sector"]:
            item["sector"] = item["sector"].title().strip()
        
        return item
    
    def _normalize_organization(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize organization fields (certificador/center)."""
        # Normalize codes
        for code_field in ["code", "certificador_code"]:
            if code_field in item and item[code_field]:
                item[code_field] = item[code_field].upper().strip()
        
        # Normalize RFC
        if "rfc" in item and item["rfc"]:
            item["rfc"] = item["rfc"].upper().strip()
        
        # Normalize state
        if "state" in item and item["state"]:
            item["state"] = self._normalize_state(item["state"])
        
        # Normalize postal code
        if "postal_code" in item and item["postal_code"]:
            item["postal_code"] = re.sub(r"\D", "", item["postal_code"])[:5]
        
        return item
    
    def _normalize_course(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize course fields."""
        # Normalize EC code
        if "ec_code" in item and item["ec_code"]:
            item["ec_code"] = item["ec_code"].upper().strip()
        
        # Normalize modality
        if "modality" in item and item["modality"]:
            modality = item["modality"].lower()
            if "línea" in modality or "online" in modality:
                item["modality"] = "en_linea"
            elif "presencial" in modality:
                item["modality"] = "presencial"
            else:
                item["modality"] = "mixto"
        
        # Parse dates
        for date_field in ["start_date", "end_date"]:
            if date_field in item and item[date_field]:
                item[date_field] = self._parse_date(item[date_field])
        
        return item
    
    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number to E.164 format."""
        try:
            # Try parsing as Mexican number
            parsed = phonenumbers.parse(phone, "MX")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass
        
        # Fallback: clean and format
        cleaned = re.sub(r"\D", "", phone)
        if len(cleaned) == 10:
            return f"+52{cleaned}"
        elif len(cleaned) == 12 and cleaned.startswith("52"):
            return f"+{cleaned}"
        
        return phone  # Return original if can't normalize
    
    def _normalize_state(self, state: str) -> str:
        """Normalize Mexican state names."""
        state_mapping = {
            "cdmx": "Ciudad de México",
            "mexico": "Estado de México",
            "edomex": "Estado de México",
            "nl": "Nuevo León",
            "bc": "Baja California",
            "bcs": "Baja California Sur",
            "qroo": "Quintana Roo",
            "qro": "Querétaro",
            # Add more mappings as needed
        }
        
        state_lower = state.lower().strip()
        return state_mapping.get(state_lower, state.title())
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d de %B de %Y",
            "%B %d, %Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _calculate_content_hash(self, item: Dict[str, Any]) -> str:
        """Calculate hash of item content."""
        # Select fields for hashing
        hash_fields = ["type", "code", "name", "title", "rfc", "ec_code"]
        content = "|".join(
            str(item.get(field, "")) for field in hash_fields if field in item
        )
        return hashlib.sha256(content.encode()).hexdigest()


class DeduplicationPipeline:
    """Remove duplicate items using Redis."""
    
    def __init__(self, redis_url: str, expire_time: int = 86400):
        self.redis_url = redis_url
        self.expire_time = expire_time
        self.redis_client = None
        self.seen_items = set()  # Local cache
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_url=crawler.settings.get("REDIS_URL"),
            expire_time=crawler.settings.getint("DEDUP_EXPIRE_TIME", 86400),
        )
    
    def open_spider(self, spider):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        logger.info("Deduplication pipeline opened")
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Check for duplicate items."""
        # Generate unique key
        item_type = item.get("type")
        content_hash = item.get("content_hash")
        
        if not content_hash:
            return item
        
        key = f"dedup:{item_type}:{content_hash}"
        
        # Check local cache first
        if key in self.seen_items:
            raise DropItem(f"Duplicate item: {key}")
        
        # Check Redis
        try:
            if self.redis_client.exists(key):
                raise DropItem(f"Duplicate item found in Redis: {key}")
            
            # Mark as seen
            self.redis_client.setex(key, self.expire_time, "1")
            self.seen_items.add(key)
            
        except redis.RedisError as e:
            logger.error(f"Redis error in deduplication: {e}")
            # Continue processing on Redis error
        
        return item


class DatabasePipeline:
    """Save items to PostgreSQL database."""
    
    def __init__(self):
        self.session = None
        self.stats = {
            "saved": 0,
            "updated": 0,
            "errors": 0,
        }
    
    def open_spider(self, spider):
        """Initialize database session."""
        logger.info("Database pipeline opened")
    
    def close_spider(self, spider):
        """Close database session and log stats."""
        logger.info(
            "Database pipeline closed",
            stats=self.stats,
            spider=spider.name,
        )
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Save item to database."""
        item_type = item.get("type")
        
        # Skip items with validation errors
        if item.get("validation_errors"):
            return item
        
        try:
            with get_session() as session:
                if item_type == "ec_standard":
                    self._save_ec_standard(session, item)
                elif item_type == "certificador":
                    self._save_certificador(session, item)
                elif item_type == "center":
                    self._save_center(session, item)
                elif item_type == "course":
                    self._save_course(session, item)
                
                session.commit()
                self.stats["saved"] += 1
                
        except IntegrityError as e:
            logger.warning(
                "Integrity error, attempting update",
                error=str(e),
                item_type=item_type,
            )
            self.stats["updated"] += 1
            
        except Exception as e:
            logger.error(
                "Database error",
                error=str(e),
                item_type=item_type,
                url=item.get("url"),
            )
            self.stats["errors"] += 1
            raise
        
        return item
    
    def _save_ec_standard(self, session, item: Dict[str, Any]):
        """Save or update EC standard."""
        ec = session.query(ECStandard).filter_by(code=item["code"]).first()
        
        if ec:
            # Update existing
            ec.last_seen = datetime.utcnow()
            for field in ["title", "sector", "level", "publication_date", "status"]:
                if field in item and item[field] is not None:
                    setattr(ec, field, item[field])
        else:
            # Create new
            ec = ECStandard(
                code=item["code"],
                title=item.get("title"),
                sector=item.get("sector"),
                level=item.get("level"),
                publication_date=item.get("publication_date"),
                status=item.get("status", "active"),
                url=item.get("url"),
                content_hash=item.get("content_hash"),
            )
            session.add(ec)
    
    def _save_certificador(self, session, item: Dict[str, Any]):
        """Save or update certificador."""
        cert = session.query(Certificador).filter_by(code=item["code"]).first()
        
        if cert:
            # Update existing
            cert.last_seen = datetime.utcnow()
            for field in ["name", "rfc", "contact_email", "contact_phone", "address", "city", "state"]:
                if field in item and item[field] is not None:
                    setattr(cert, field, item[field])
        else:
            # Create new
            cert = Certificador(
                code=item["code"],
                name=item["name"],
                rfc=item.get("rfc"),
                contact_email=item.get("contact_email"),
                contact_phone=item.get("contact_phone"),
                address=item.get("address"),
                city=item.get("city"),
                state=item.get("state"),
                url=item.get("url"),
                content_hash=item.get("content_hash"),
            )
            session.add(cert)
    
    def _save_center(self, session, item: Dict[str, Any]):
        """Save or update evaluation center."""
        center = session.query(EvaluationCenter).filter_by(code=item["code"]).first()
        
        if center:
            # Update existing
            center.last_seen = datetime.utcnow()
            for field in ["name", "certificador_code", "contact_email", "contact_phone", "address"]:
                if field in item and item[field] is not None:
                    setattr(center, field, item[field])
        else:
            # Find certificador
            certificador = session.query(Certificador).filter_by(
                code=item["certificador_code"]
            ).first()
            
            # Create new center
            center = EvaluationCenter(
                code=item["code"],
                name=item["name"],
                certificador_id=certificador.id if certificador else None,
                certificador_code=item.get("certificador_code"),
                contact_email=item.get("contact_email"),
                contact_phone=item.get("contact_phone"),
                address=item.get("address"),
                city=item.get("city"),
                state=item.get("state"),
                url=item.get("url"),
                content_hash=item.get("content_hash"),
            )
            session.add(center)
    
    def _save_course(self, session, item: Dict[str, Any]):
        """Save or update course."""
        # Find related EC standard
        ec_standard = None
        if item.get("ec_code"):
            ec_standard = session.query(ECStandard).filter_by(
                code=item["ec_code"]
            ).first()
        
        # Create course (courses are not unique by any field)
        course = Course(
            name=item["name"],
            ec_standard_id=ec_standard.id if ec_standard else None,
            ec_code=item.get("ec_code"),
            duration_hours=item.get("duration_hours"),
            modality=item.get("modality"),
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            provider_name=item.get("provider_name"),
            city=item.get("city"),
            state=item.get("state"),
            url=item.get("url"),
            content_hash=item.get("content_hash"),
        )
        session.add(course)


class CachePipeline:
    """Cache processed items in Redis for quick access."""
    
    def __init__(self, redis_url: str, cache_ttl: int = 3600):
        self.redis_url = redis_url
        self.cache_ttl = cache_ttl
        self.redis_client = None
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_url=crawler.settings.get("REDIS_URL"),
            cache_ttl=crawler.settings.getint("CACHE_TTL", 3600),
        )
    
    def open_spider(self, spider):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        logger.info("Cache pipeline opened")
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Cache item in Redis."""
        item_type = item.get("type")
        
        # Generate cache keys
        if item_type == "ec_standard" and item.get("code"):
            key = f"cache:ec:{item['code']}"
        elif item_type == "certificador" and item.get("code"):
            key = f"cache:cert:{item['code']}"
        elif item_type == "center" and item.get("code"):
            key = f"cache:center:{item['code']}"
        else:
            return item
        
        try:
            # Cache as JSON
            import json
            self.redis_client.setex(
                key,
                self.cache_ttl,
                json.dumps(item, default=str),
            )
            
        except redis.RedisError as e:
            logger.error(f"Redis cache error: {e}")
        
        return item
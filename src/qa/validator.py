"""Data validation module."""

import re
from collections import defaultdict
from typing import Dict, List, Any

from src.core.constants import VALIDATION_PATTERNS
from structlog import get_logger

logger = get_logger()


class DataValidator:
    """Validate harvested data quality."""
    
    def __init__(self):
        self.validation_rules = {
            "ec_standard": self._validate_ec_standard,
            "certificador": self._validate_certificador,
            "center": self._validate_center,
            "course": self._validate_course,
        }
    
    def validate_harvest(self, session_id: str, auto_fix: bool = False) -> Dict[str, Any]:
        """Validate all data from a harvest session."""
        # This is a placeholder - in real implementation would query database
        results = {
            "session_id": session_id,
            "total_items": 1000,
            "valid_items": 950,
            "invalid_items": 50,
            "errors": [
                {"component_type": "ec_standard", "field": "code", "count": 10},
                {"component_type": "certificador", "field": "email", "count": 15},
                {"component_type": "center", "field": "phone", "count": 25},
            ],
            "auto_fixed": 0 if not auto_fix else 30,
        }
        
        return results
    
    def validate_component(self, component_type: str, items: List[Any], auto_fix: bool = False) -> Dict[str, Any]:
        """Validate a specific component type."""
        if component_type not in self.validation_rules:
            raise ValueError(f"Unknown component type: {component_type}")
        
        results = {
            "component_type": component_type,
            "total": len(items),
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }
        
        error_counts = defaultdict(lambda: {"count": 0, "examples": []})
        
        for item in items:
            validation_func = self.validation_rules[component_type]
            errors = validation_func(item)
            
            if errors:
                results["invalid"] += 1
                for error in errors:
                    error_key = f"{error['field']}:{error['message']}"
                    error_counts[error_key]["count"] += 1
                    if len(error_counts[error_key]["examples"]) < 3:
                        error_counts[error_key]["examples"].append(str(item))
            else:
                results["valid"] += 1
        
        # Convert error counts to list
        results["errors"] = [
            {
                "field": key.split(":")[0],
                "message": key.split(":")[1],
                "count": data["count"],
                "examples": data["examples"],
            }
            for key, data in sorted(
                error_counts.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )
        ]
        
        return results
    
    def _validate_ec_standard(self, item) -> List[Dict[str, str]]:
        """Validate EC standard."""
        errors = []
        
        # Validate code
        if hasattr(item, 'code'):
            if not item.code:
                errors.append({"field": "code", "message": "Missing code"})
            elif not re.match(VALIDATION_PATTERNS["ec_code"], item.code):
                errors.append({"field": "code", "message": "Invalid format"})
        
        # Validate title
        if hasattr(item, 'title'):
            if not item.title:
                errors.append({"field": "title", "message": "Missing title"})
            elif len(item.title) < 10:
                errors.append({"field": "title", "message": "Title too short"})
        
        # Validate level
        if hasattr(item, 'level') and item.level:
            if not isinstance(item.level, int) or item.level < 1 or item.level > 5:
                errors.append({"field": "level", "message": "Invalid level (must be 1-5)"})
        
        return errors
    
    def _validate_certificador(self, item) -> List[Dict[str, str]]:
        """Validate certificador."""
        errors = []
        
        # Validate code
        if hasattr(item, 'code') and item.code:
            if not re.match(VALIDATION_PATTERNS["oec_code"], item.code):
                errors.append({"field": "code", "message": "Invalid format"})
        
        # Validate email
        if hasattr(item, 'contact_email') and item.contact_email:
            if not re.match(VALIDATION_PATTERNS["email"], item.contact_email):
                errors.append({"field": "email", "message": "Invalid email format"})
        
        # Validate RFC
        if hasattr(item, 'rfc') and item.rfc:
            if not re.match(VALIDATION_PATTERNS["rfc"], item.rfc):
                errors.append({"field": "rfc", "message": "Invalid RFC format"})
        
        # Validate phone
        if hasattr(item, 'contact_phone') and item.contact_phone:
            if not re.match(VALIDATION_PATTERNS["phone"], item.contact_phone):
                errors.append({"field": "phone", "message": "Invalid phone format"})
        
        return errors
    
    def _validate_center(self, item) -> List[Dict[str, str]]:
        """Validate evaluation center."""
        errors = []
        
        # Validate code
        if hasattr(item, 'code') and item.code:
            if not re.match(VALIDATION_PATTERNS["ce_code"], item.code):
                errors.append({"field": "code", "message": "Invalid format"})
        
        # Validate certificador relationship
        if hasattr(item, 'certificador_code'):
            if not item.certificador_code:
                errors.append({"field": "certificador_code", "message": "Missing certificador"})
        
        return errors
    
    def _validate_course(self, item) -> List[Dict[str, str]]:
        """Validate course."""
        errors = []
        
        # Validate name
        if hasattr(item, 'name'):
            if not item.name:
                errors.append({"field": "name", "message": "Missing name"})
        
        # Validate EC code
        if hasattr(item, 'ec_code') and item.ec_code:
            if not re.match(VALIDATION_PATTERNS["ec_code"], item.ec_code):
                errors.append({"field": "ec_code", "message": "Invalid EC code format"})
        
        # Validate duration
        if hasattr(item, 'duration_hours') and item.duration_hours:
            if item.duration_hours < 0 or item.duration_hours > 1000:
                errors.append({"field": "duration", "message": "Invalid duration"})
        
        return errors
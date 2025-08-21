"""
Data validator for RENEC harvested data.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from .expectations import ValidationExpectations


logger = logging.getLogger(__name__)


class DataValidator:
    """Validates harvested data against quality expectations."""
    
    def __init__(self, expectations: Optional[ValidationExpectations] = None):
        """
        Initialize validator with expectations.
        
        Args:
            expectations: Validation expectations or use defaults
        """
        self.expectations = expectations or ValidationExpectations()
        self.validation_stats = defaultdict(int)
        self.validation_errors = []
        
    def validate_item(self, item: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single item.
        
        Args:
            item: Item dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        entity_type = self.expectations.get_entity_type(item)
        
        # Track entity type
        self.validation_stats[f'{entity_type}_total'] += 1
        
        # Validate required fields
        if entity_type in self.expectations.REQUIRED_FIELDS:
            for field in self.expectations.REQUIRED_FIELDS[entity_type]:
                if not item.get(field):
                    errors.append(f"Missing required field: {field}")
        
        # Entity-specific validation
        if entity_type == 'ec_standard':
            errors.extend(self._validate_ec_standard(item))
        elif entity_type == 'certificador':
            errors.extend(self._validate_certificador(item))
        elif entity_type == 'sector':
            errors.extend(self._validate_sector(item))
        elif entity_type == 'comite':
            errors.extend(self._validate_comite(item))
        elif entity_type == 'centro':
            errors.extend(self._validate_centro(item))
        elif entity_type in ['ece_ec_relation', 'centro_ec_relation']:
            errors.extend(self._validate_relation(item))
        
        # Validate field lengths
        for field_name, value in item.items():
            if not self.expectations.validate_field_length(field_name, value):
                errors.append(f"Field {field_name} exceeds maximum length")
        
        # Update stats
        if errors:
            self.validation_stats[f'{entity_type}_invalid'] += 1
            self.validation_errors.append({
                'entity_type': entity_type,
                'item': item,
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            })
        else:
            self.validation_stats[f'{entity_type}_valid'] += 1
        
        return len(errors) == 0, errors
    
    def _validate_ec_standard(self, item: Dict[str, Any]) -> List[str]:
        """Validate EC standard specific rules."""
        errors = []
        
        # Validate EC code format
        if not self.expectations.validate_ec_code(item.get('ec_clave', '')):
            errors.append(f"Invalid EC code format: {item.get('ec_clave')}")
        
        # Validate title length
        titulo = item.get('titulo', '')
        if len(titulo) < self.expectations.EC_TITLE_MIN_LENGTH:
            errors.append(f"Title too short: {len(titulo)} chars")
        elif len(titulo) > self.expectations.EC_TITLE_MAX_LENGTH:
            errors.append(f"Title too long: {len(titulo)} chars")
        
        # Validate version format
        version = item.get('version')
        if version and not re.match(self.expectations.EC_VERSION_PATTERN, str(version)):
            errors.append(f"Invalid version format: {version}")
        
        # Validate dates
        for date_field in ['fecha_publicacion', 'fecha_vigencia']:
            if date_field in item and item[date_field]:
                if not self.expectations.validate_date_range(item[date_field]):
                    errors.append(f"Invalid {date_field}: {item[date_field]}")
        
        # Validate URL
        if not self.expectations.validate_url(item.get('renec_url', '')):
            errors.append("Invalid or missing RENEC URL")
        
        # Validate sector/committee IDs if present
        if item.get('sector_id') and not str(item['sector_id']).isdigit():
            errors.append(f"Invalid sector_id: {item['sector_id']}")
        
        if item.get('comite_id') and not str(item['comite_id']).isdigit():
            errors.append(f"Invalid comite_id: {item['comite_id']}")
        
        return errors
    
    def _validate_certificador(self, item: Dict[str, Any]) -> List[str]:
        """Validate certificador specific rules."""
        errors = []
        
        # Validate type
        if item.get('tipo') not in self.expectations.CERT_TYPES:
            errors.append(f"Invalid certificador type: {item.get('tipo')}")
        
        # Validate status
        if item.get('estatus') and item['estatus'] not in self.expectations.CERT_STATUS_VALUES:
            errors.append(f"Invalid status: {item.get('estatus')}")
        
        # Validate INEGI code
        if item.get('estado_inegi') and not self.expectations.validate_inegi_code(item['estado_inegi']):
            errors.append(f"Invalid INEGI state code: {item.get('estado_inegi')}")
        
        # Validate postal code
        if item.get('cp') and not self.expectations.validate_postal_code(item['cp']):
            errors.append(f"Invalid postal code: {item.get('cp')}")
        
        # Validate phone
        if item.get('telefono') and not self.expectations.validate_phone(item['telefono']):
            errors.append(f"Invalid phone format: {item.get('telefono')}")
        
        # Validate email
        if item.get('correo') and not self.expectations.validate_email(item['correo']):
            errors.append(f"Invalid email format: {item.get('correo')}")
        
        # Validate website URL
        if item.get('sitio_web') and not self.expectations.validate_url(item['sitio_web']):
            errors.append(f"Invalid website URL: {item.get('sitio_web')}")
        
        # Validate accreditation date
        if item.get('fecha_acreditacion') and not self.expectations.validate_date_range(item['fecha_acreditacion']):
            errors.append(f"Invalid accreditation date: {item.get('fecha_acreditacion')}")
        
        # Validate EC standards list
        if item.get('estandares_acreditados'):
            if not isinstance(item['estandares_acreditados'], list):
                errors.append("estandares_acreditados must be a list")
            else:
                for ec_code in item['estandares_acreditados']:
                    if not self.expectations.validate_ec_code(ec_code):
                        errors.append(f"Invalid EC code in list: {ec_code}")
        
        return errors
    
    def _validate_sector(self, item: Dict[str, Any]) -> List[str]:
        """Validate sector specific rules."""
        errors = []
        
        # Validate sector ID is numeric
        if not str(item.get('sector_id', '')).isdigit():
            errors.append(f"Invalid sector_id: {item.get('sector_id')}")
        
        # Validate name is not empty
        if not item.get('nombre', '').strip():
            errors.append("Sector name cannot be empty")
        
        # Validate URL
        if not self.expectations.validate_url(item.get('src_url', '')):
            errors.append("Invalid or missing source URL")
        
        return errors
    
    def _validate_comite(self, item: Dict[str, Any]) -> List[str]:
        """Validate committee specific rules."""
        errors = []
        
        # Validate committee ID is numeric
        if not str(item.get('comite_id', '')).isdigit():
            errors.append(f"Invalid comite_id: {item.get('comite_id')}")
        
        # Validate name is not empty
        if not item.get('nombre', '').strip():
            errors.append("Committee name cannot be empty")
        
        # Validate sector reference if present
        if item.get('sector_id') and not str(item['sector_id']).isdigit():
            errors.append(f"Invalid sector_id reference: {item['sector_id']}")
        
        # Validate URL
        if not self.expectations.validate_url(item.get('src_url', '')):
            errors.append("Invalid or missing source URL")
        
        return errors
    
    def _validate_centro(self, item: Dict[str, Any]) -> List[str]:
        """Validate center specific rules."""
        errors = []
        
        # Validate center ID format
        if not item.get('centro_id'):
            errors.append("Missing centro_id")
        
        # Validate name is not empty
        if not item.get('nombre', '').strip():
            errors.append("Center name cannot be empty")
        
        # Validate certificador reference if present
        if item.get('cert_id') and not item['cert_id'].strip():
            errors.append("Invalid certificador reference")
        
        # Validate INEGI code
        if item.get('estado_inegi') and not self.expectations.validate_inegi_code(item['estado_inegi']):
            errors.append(f"Invalid INEGI state code: {item.get('estado_inegi')}")
        
        # Validate postal code
        if item.get('cp') and not self.expectations.validate_postal_code(item['cp']):
            errors.append(f"Invalid postal code: {item.get('cp')}")
        
        # Validate phone
        if item.get('telefono') and not self.expectations.validate_phone(item['telefono']):
            errors.append(f"Invalid phone format: {item.get('telefono')}")
        
        # Validate email
        if item.get('correo') and not self.expectations.validate_email(item['correo']):
            errors.append(f"Invalid email format: {item.get('correo')}")
        
        # Validate URL
        if not self.expectations.validate_url(item.get('src_url', '')):
            errors.append("Invalid or missing source URL")
        
        return errors
    
    def _validate_relation(self, item: Dict[str, Any]) -> List[str]:
        """Validate relationship records."""
        errors = []
        
        # Validate EC code in relationships
        if 'ec_clave' in item and not self.expectations.validate_ec_code(item['ec_clave']):
            errors.append(f"Invalid EC code: {item.get('ec_clave')}")
        
        # Validate IDs are not empty
        for id_field in ['cert_id', 'centro_id']:
            if id_field in item and not item[id_field]:
                errors.append(f"Empty {id_field} in relationship")
        
        # Validate date if present
        if item.get('acreditado_desde') and not self.expectations.validate_date_range(item['acreditado_desde']):
            errors.append(f"Invalid accreditation date: {item.get('acreditado_desde')}")
        
        return errors
    
    def validate_batch(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of items.
        
        Args:
            items: List of items to validate
            
        Returns:
            Validation summary report
        """
        # Reset stats for this batch
        self.validation_stats = defaultdict(int)
        self.validation_errors = []
        
        # Validate each item
        for item in items:
            self.validate_item(item)
        
        # Generate summary report
        return self.generate_validation_report()
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate validation summary report."""
        total_items = sum(v for k, v in self.validation_stats.items() if k.endswith('_total'))
        total_valid = sum(v for k, v in self.validation_stats.items() if k.endswith('_valid'))
        total_invalid = sum(v for k, v in self.validation_stats.items() if k.endswith('_invalid'))
        
        report = {
            'summary': {
                'total_items': total_items,
                'valid_items': total_valid,
                'invalid_items': total_invalid,
                'validation_rate': total_valid / total_items if total_items > 0 else 0
            },
            'by_entity_type': {},
            'coverage_status': self._check_coverage_expectations(),
            'common_errors': self._analyze_common_errors(),
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # Breakdown by entity type
        entity_types = set(k.split('_')[0] for k in self.validation_stats.keys() if '_' in k)
        for entity_type in entity_types:
            total = self.validation_stats.get(f'{entity_type}_total', 0)
            valid = self.validation_stats.get(f'{entity_type}_valid', 0)
            invalid = self.validation_stats.get(f'{entity_type}_invalid', 0)
            
            report['by_entity_type'][entity_type] = {
                'total': total,
                'valid': valid,
                'invalid': invalid,
                'validation_rate': valid / total if total > 0 else 0
            }
        
        # Add sample errors (limit to 10)
        report['sample_errors'] = self.validation_errors[:10]
        
        return report
    
    def _check_coverage_expectations(self) -> Dict[str, bool]:
        """Check if coverage expectations are met."""
        return {
            'ec_standards': self.validation_stats.get('ec_standard_total', 0) >= self.expectations.MIN_EC_STANDARDS,
            'certificadores': self.validation_stats.get('certificador_total', 0) >= self.expectations.MIN_CERTIFICADORES,
            'sectors': self.validation_stats.get('sector_total', 0) >= self.expectations.MIN_SECTORS,
            'committees': self.validation_stats.get('comite_total', 0) >= self.expectations.MIN_COMMITTEES,
            'centers': self.validation_stats.get('centro_total', 0) >= self.expectations.MIN_CENTERS
        }
    
    def _analyze_common_errors(self) -> List[Dict[str, Any]]:
        """Analyze and return most common validation errors."""
        error_counts = defaultdict(int)
        
        for error_record in self.validation_errors:
            for error in error_record['errors']:
                error_counts[error] += 1
        
        # Sort by frequency and return top 10
        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return [
            {'error': error, 'count': count}
            for error, count in sorted_errors
        ]
    
    def save_validation_report(self, report: Dict[str, Any], filepath: str):
        """Save validation report to file."""
        import json
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Validation report saved to {filepath}")


# Import re module for regex validation
import re
"""
Validation expectations for RENEC data quality.
"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationExpectations:
    """Defines expected data quality rules for RENEC components."""
    
    # Coverage expectations
    MIN_EC_STANDARDS: int = 1000
    MIN_CERTIFICADORES: int = 100
    MIN_SECTORS: int = 10
    MIN_COMMITTEES: int = 50
    MIN_CENTERS: int = 500
    
    # EC Standards validation rules
    EC_CODE_PATTERN: str = r'^EC\d{4}$'
    EC_TITLE_MIN_LENGTH: int = 10
    EC_TITLE_MAX_LENGTH: int = 500
    EC_VERSION_PATTERN: str = r'^\d+(\.\d+)?$'
    
    # Certificador validation rules
    CERT_TYPES: List[str] = field(default_factory=lambda: ['ECE', 'OC'])
    CERT_STATUS_VALUES: List[str] = field(default_factory=lambda: ['ACTIVO', 'INACTIVO', 'SUSPENDIDO'])
    PHONE_PATTERN: str = r'^\+?52\d{10}$'
    EMAIL_PATTERN: str = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    CP_PATTERN: str = r'^\d{5}$'
    
    # INEGI state codes
    VALID_INEGI_CODES: List[str] = field(default_factory=lambda: [
        '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
        '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
        '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
        '31', '32'
    ])
    
    # Date validation
    MIN_DATE: datetime = datetime(2000, 1, 1)
    MAX_DATE: datetime = datetime(2050, 12, 31)
    
    # Required fields by entity type
    REQUIRED_FIELDS: Dict[str, List[str]] = field(default_factory=lambda: {
        'ec_standard': ['ec_clave', 'titulo', 'renec_url'],
        'certificador': ['cert_id', 'tipo', 'nombre_legal', 'src_url'],
        'sector': ['sector_id', 'nombre', 'src_url'],
        'comite': ['comite_id', 'nombre', 'src_url'],
        'centro': ['centro_id', 'nombre', 'src_url'],
        'ece_ec_relation': ['cert_id', 'ec_clave'],
        'centro_ec_relation': ['centro_id', 'ec_clave']
    })
    
    # Field length constraints
    FIELD_MAX_LENGTHS: Dict[str, int] = field(default_factory=lambda: {
        'ec_clave': 10,
        'cert_id': 50,
        'centro_id': 50,
        'siglas': 50,
        'nivel': 50,
        'tipo_norma': 50,
        'estado': 50,
        'estado_inegi': 2,
        'municipio': 100,
        'cp': 5,
        'telefono': 20,
        'correo': 100,
        'sitio_web': 200,
        'representante_legal': 200,
        'nombre': 200,
        'nombre_legal': 500,
        'titulo': 1000,
        'descripcion': 5000,
        'perfil_evaluador': 2000
    })
    
    def get_entity_type(self, item: Dict[str, Any]) -> str:
        """Determine entity type from item data."""
        if 'type' in item:
            return item['type']
        elif 'ec_clave' in item and 'titulo' in item:
            return 'ec_standard'
        elif 'cert_id' in item and 'tipo' in item:
            return 'certificador'
        elif 'sector_id' in item:
            return 'sector'
        elif 'comite_id' in item:
            return 'comite'
        elif 'centro_id' in item:
            return 'centro'
        else:
            return 'unknown'
    
    def validate_ec_code(self, code: str) -> bool:
        """Validate EC code format."""
        if not code:
            return False
        return bool(re.match(self.EC_CODE_PATTERN, code))
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return True  # Optional field
        return bool(re.match(self.EMAIL_PATTERN, email.lower()))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate Mexican phone number."""
        if not phone:
            return True  # Optional field
        # Remove non-digits for validation
        digits = re.sub(r'\D', '', phone)
        return len(digits) in [10, 12, 13]
    
    def validate_postal_code(self, cp: str) -> bool:
        """Validate Mexican postal code."""
        if not cp:
            return True  # Optional field
        return bool(re.match(self.CP_PATTERN, cp))
    
    def validate_inegi_code(self, code: str) -> bool:
        """Validate INEGI state code."""
        if not code:
            return True  # Optional field
        return code in self.VALID_INEGI_CODES
    
    def validate_date_range(self, date_str: str) -> bool:
        """Validate date is within reasonable range."""
        if not date_str:
            return True  # Optional field
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            return self.MIN_DATE <= date <= self.MAX_DATE
        except ValueError:
            return False
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        if not url:
            return False  # Required field
        return url.startswith('http://') or url.startswith('https://')
    
    def validate_field_length(self, field_name: str, value: Any) -> bool:
        """Validate field doesn't exceed maximum length."""
        if field_name not in self.FIELD_MAX_LENGTHS:
            return True
        
        if value is None:
            return True
            
        str_value = str(value)
        return len(str_value) <= self.FIELD_MAX_LENGTHS[field_name]
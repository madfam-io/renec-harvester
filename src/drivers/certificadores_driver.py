"""
Certificadores driver for extracting ECE/OC entities from RENEC.
"""
import re
import json
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime
import logging

from scrapy.http import Response
from scrapy import Request

from .base_driver import BaseDriver

logger = logging.getLogger(__name__)


class CertificadoresDriver(BaseDriver):
    """Driver for extracting Certificadores (ECE/OC) data with modal handling."""
    
    # RENEC endpoints for certificadores
    CERT_ENDPOINTS = {
        'ece_list': '/RENEC/controlador.do?comp=ECE',
        'oc_list': '/RENEC/controlador.do?comp=OC',
        'detail': '/RENEC/controlador.do?comp=CERT&id={}',
        'modal_standards': '/RENEC/controlador.do?comp=CERT_EC&id={}',
        'modal_contact': '/RENEC/controlador.do?comp=CERT_CONTACT&id={}'
    }
    
    # State name to INEGI code mapping
    ESTADO_INEGI_MAP = {
        'AGUASCALIENTES': '01',
        'BAJA CALIFORNIA': '02',
        'BAJA CALIFORNIA SUR': '03',
        'CAMPECHE': '04',
        'COAHUILA': '05',
        'COLIMA': '06',
        'CHIAPAS': '07',
        'CHIHUAHUA': '08',
        'CIUDAD DE MÉXICO': '09',
        'DURANGO': '10',
        'GUANAJUATO': '11',
        'GUERRERO': '12',
        'HIDALGO': '13',
        'JALISCO': '14',
        'MÉXICO': '15',
        'MICHOACÁN': '16',
        'MORELOS': '17',
        'NAYARIT': '18',
        'NUEVO LEÓN': '19',
        'OAXACA': '20',
        'PUEBLA': '21',
        'QUERÉTARO': '22',
        'QUINTANA ROO': '23',
        'SAN LUIS POTOSÍ': '24',
        'SINALOA': '25',
        'SONORA': '26',
        'TABASCO': '27',
        'TAMAULIPAS': '28',
        'TLAXCALA': '29',
        'VERACRUZ': '30',
        'YUCATÁN': '31',
        'ZACATECAS': '32'
    }
    
    def get_start_urls(self) -> List[str]:
        """Get initial URLs for certificadores extraction."""
        base_url = 'https://conocer.gob.mx'
        
        # Start with both ECE and OC listings
        return [
            base_url + self.CERT_ENDPOINTS['ece_list'],
            base_url + self.CERT_ENDPOINTS['oc_list']
        ]
    
    def parse(self, response: Response) -> Generator[Any, None, None]:
        """Parse certificador listing page."""
        self.update_stats('pages_processed')
        
        try:
            # Determine type (ECE or OC)
            cert_type = self._determine_cert_type(response.url)
            logger.info(f"Parsing {cert_type} listing")
            
            # Extract certificador entries
            cert_entries = self._extract_certificador_list(response)
            
            for entry in cert_entries:
                entry['tipo'] = cert_type
                
                # Create detail page request if ID available
                if entry.get('cert_id'):
                    detail_url = self._build_detail_url(entry['cert_id'])
                    
                    yield self.create_request(
                        url=detail_url,
                        callback=self.parse_detail,
                        meta={'cert_data': entry},
                        priority=5
                    )
                else:
                    # If no detail page, yield what we have
                    if self.validate_item(entry):
                        self.update_stats('items_extracted')
                        yield entry
            
            # Handle pagination
            next_page = self.handle_pagination(response)
            if next_page:
                yield next_page
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def parse_detail(self, response: Response) -> Dict[str, Any]:
        """Parse certificador detail page including modal data."""
        self.update_stats('pages_processed')
        
        try:
            # Get basic data from listing
            cert_data = response.meta.get('cert_data', {})
            
            # Extract detailed information
            detail_data = {
                'cert_id': cert_data.get('cert_id'),
                'tipo': cert_data.get('tipo'),
                'nombre_legal': self._extract_nombre_legal(response),
                'siglas': self._extract_siglas(response),
                'estatus': self._extract_estatus(response),
                'domicilio_texto': self._extract_domicilio(response),
                'estado': self._extract_estado(response),
                'municipio': self._extract_municipio(response),
                'cp': self._extract_cp(response),
                'telefono': self._extract_telefono(response),
                'correo': self._extract_correo(response),
                'sitio_web': self._extract_sitio_web(response),
                'representante_legal': self._extract_representante(response),
                'fecha_acreditacion': self._extract_fecha_acreditacion(response),
                'src_url': response.url,
                'extracted_at': datetime.now().isoformat()
            }
            
            # Normalize state to INEGI code
            if detail_data.get('estado'):
                detail_data['estado_inegi'] = self._normalize_estado_inegi(detail_data['estado'])
            
            # Extract modal data (standards and additional contacts)
            modal_data = self._extract_modal_data(response, cert_data.get('cert_id'))
            detail_data.update(modal_data)
            
            # Merge with listing data
            detail_data.update(cert_data)
            
            # Clean and validate
            detail_data = self._clean_cert_data(detail_data)
            
            # Compute content hash
            detail_data['row_hash'] = self.compute_content_hash(detail_data)
            
            if self.validate_item(detail_data):
                self.update_stats('items_extracted')
                
                # Yield main certificador item
                yield detail_data
                
                # Yield EC relationships if found
                if detail_data.get('estandares_acreditados'):
                    for ec_relation in self._create_ec_relationships(detail_data):
                        yield ec_relation
            else:
                logger.warning(f"Invalid certificador item: {detail_data.get('cert_id')}")
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def _determine_cert_type(self, url: str) -> str:
        """Determine certificador type from URL."""
        if 'comp=ECE' in url:
            return 'ECE'
        elif 'comp=OC' in url:
            return 'OC'
        else:
            return 'UNKNOWN'
    
    def _extract_certificador_list(self, response: Response) -> List[Dict[str, Any]]:
        """Extract certificador entries from listing page."""
        certificadores = []
        
        # Try table format first
        rows = response.xpath('//table[@class="table"]//tr[position()>1]')
        
        if rows:
            for row in rows:
                cert = self._parse_table_row(row)
                if cert:
                    certificadores.append(cert)
        else:
            # Try card/div format
            cards = response.xpath('//div[@class="certificador-card"]')
            for card in cards:
                cert = self._parse_card_format(card)
                if cert:
                    certificadores.append(cert)
        
        return certificadores
    
    def _parse_table_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse certificador from table row."""
        try:
            # Extract ID from link or data attribute
            cert_link = row.xpath('.//a[contains(@href, "id=")]/@href').get()
            cert_id = None
            
            if cert_link:
                match = re.search(r'id=(\w+)', cert_link)
                if match:
                    cert_id = match.group(1)
            
            if not cert_id:
                cert_id = row.xpath('.//@data-id').get()
            
            return {
                'cert_id': cert_id,
                'nombre_legal': self.clean_text(
                    row.xpath('.//td[1]//text()').get()
                ),
                'siglas': self.clean_text(
                    row.xpath('.//td[2]//text()').get()
                ),
                'estado': self.clean_text(
                    row.xpath('.//td[3]//text()').get()
                ),
                'estatus': self.clean_text(
                    row.xpath('.//td[4]//text()').get()
                )
            }
        except Exception as e:
            logger.warning(f"Failed to parse table row: {e}")
            return None
    
    def _parse_card_format(self, card) -> Optional[Dict[str, Any]]:
        """Parse certificador from card/div format."""
        try:
            cert_id = card.xpath('.//@data-cert-id').get()
            
            return {
                'cert_id': cert_id,
                'nombre_legal': self.clean_text(
                    card.xpath('.//h3[@class="cert-name"]//text()').get()
                ),
                'siglas': self.clean_text(
                    card.xpath('.//span[@class="cert-siglas"]//text()').get()
                ),
                'estado': self.clean_text(
                    card.xpath('.//span[@class="cert-estado"]//text()').get()
                ),
                'estatus': self.clean_text(
                    card.xpath('.//span[@class="cert-status"]//text()').get()
                )
            }
        except Exception as e:
            logger.warning(f"Failed to parse card format: {e}")
            return None
    
    def _build_detail_url(self, cert_id: str) -> str:
        """Build detail page URL for certificador."""
        base_url = 'https://conocer.gob.mx'
        return base_url + self.CERT_ENDPOINTS['detail'].format(cert_id)
    
    def _extract_nombre_legal(self, response: Response) -> str:
        """Extract legal name."""
        selectors = [
            '//td[contains(text(), "Nombre")]/following-sibling::td//text()',
            '//h1[@class="cert-title"]//text()',
            '//div[@class="nombre-legal"]//text()'
        ]
        
        for selector in selectors:
            nombre = self.extract_text(response, selector)
            if nombre:
                return self.clean_text(nombre)
        
        return ''
    
    def _extract_siglas(self, response: Response) -> str:
        """Extract abbreviation."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Siglas")]/following-sibling::td//text()'
            )
        )
    
    def _extract_estatus(self, response: Response) -> str:
        """Extract status."""
        status = self.extract_text(
            response,
            '//td[contains(text(), "Estatus")]/following-sibling::td//text()'
        )
        
        if not status:
            status = self.extract_text(response, '//span[@class="status"]//text()')
        
        return self.clean_text(status) or 'ACTIVO'
    
    def _extract_domicilio(self, response: Response) -> str:
        """Extract full address."""
        selectors = [
            '//td[contains(text(), "Domicilio")]/following-sibling::td//text()',
            '//div[@class="domicilio"]//text()'
        ]
        
        for selector in selectors:
            texts = response.xpath(selector).getall()
            if texts:
                return self.clean_text(' '.join(texts))
        
        return ''
    
    def _extract_estado(self, response: Response) -> str:
        """Extract state name."""
        estado = self.extract_text(
            response,
            '//td[contains(text(), "Estado")]/following-sibling::td//text()'
        )
        
        if not estado and response.meta.get('cert_data'):
            estado = response.meta['cert_data'].get('estado', '')
        
        return self.clean_text(estado).upper()
    
    def _extract_municipio(self, response: Response) -> str:
        """Extract municipality."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Municipio")]/following-sibling::td//text()'
            )
        )
    
    def _extract_cp(self, response: Response) -> str:
        """Extract postal code."""
        cp_text = self.extract_text(
            response,
            '//td[contains(text(), "C.P.")]/following-sibling::td//text()'
        )
        
        if not cp_text:
            # Try to extract from address
            domicilio = self._extract_domicilio(response)
            match = re.search(r'C\.?P\.?\s*(\d{5})', domicilio)
            if match:
                return match.group(1)
        
        # Clean to just digits
        return re.sub(r'\D', '', cp_text)[:5]
    
    def _extract_telefono(self, response: Response) -> str:
        """Extract and normalize phone number."""
        phone = self.extract_text(
            response,
            '//td[contains(text(), "Teléfono")]/following-sibling::td//text()'
        )
        
        if phone:
            return self._normalize_phone(phone)
        
        return ''
    
    def _extract_correo(self, response: Response) -> str:
        """Extract email address."""
        email = self.extract_text(
            response,
            '//td[contains(text(), "Correo")]/following-sibling::td//text()'
        )
        
        if not email:
            email = self.extract_text(response, '//a[contains(@href, "mailto:")]//text()')
        
        return self.clean_text(email).lower()
    
    def _extract_sitio_web(self, response: Response) -> str:
        """Extract website URL."""
        website = self.extract_text(
            response,
            '//td[contains(text(), "Sitio")]/following-sibling::td//a/@href'
        )
        
        if not website:
            website = self.extract_text(
                response,
                '//td[contains(text(), "Sitio")]/following-sibling::td//text()'
            )
        
        if website and not website.startswith('http'):
            website = 'http://' + website
        
        return website
    
    def _extract_representante(self, response: Response) -> str:
        """Extract legal representative name."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Representante")]/following-sibling::td//text()'
            )
        )
    
    def _extract_fecha_acreditacion(self, response: Response) -> Optional[str]:
        """Extract accreditation date."""
        date_text = self.extract_text(
            response,
            '//td[contains(text(), "Acreditación")]/following-sibling::td//text()'
        )
        
        if date_text:
            return self._parse_date(date_text)
        
        return None
    
    def _extract_modal_data(self, response: Response, cert_id: str) -> Dict[str, Any]:
        """Extract data from modals (standards, contacts)."""
        modal_data = {}
        
        # Look for JavaScript data containing modal information
        scripts = response.xpath('//script[contains(text(), "modalData")]//text()').getall()
        
        for script in scripts:
            # Try to extract JSON data
            json_match = re.search(r'modalData\s*=\s*({.*?});', script, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    
                    # Extract standards
                    if 'standards' in data:
                        modal_data['estandares_acreditados'] = [
                            std.get('code') for std in data['standards']
                            if std.get('code') and re.match(r'^EC\d{4}$', std.get('code'))
                        ]
                    
                    # Extract additional contacts
                    if 'contacts' in data:
                        modal_data['contactos_adicionales'] = data['contacts']
                        
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse modal JSON for cert {cert_id}")
        
        # Alternative: Look for modal content in HTML
        if not modal_data.get('estandares_acreditados'):
            ec_codes = response.xpath(
                '//div[@class="modal-estandares"]//span[@class="ec-code"]//text()'
            ).getall()
            
            if ec_codes:
                modal_data['estandares_acreditados'] = [
                    code.strip() for code in ec_codes
                    if re.match(r'^EC\d{4}$', code.strip())
                ]
        
        return modal_data
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize Mexican phone numbers."""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10:
            # Standard 10-digit Mexican number
            return f"+52{digits}"
        elif len(digits) == 12 and digits.startswith('52'):
            # Already has country code
            return f"+{digits}"
        elif len(digits) == 13 and digits.startswith('052'):
            # Has 0 prefix
            return f"+52{digits[3:]}"
        else:
            # Return cleaned version
            return digits
    
    def _normalize_estado_inegi(self, estado: str) -> str:
        """Convert state name to INEGI code."""
        estado_upper = estado.upper().strip()
        
        # Direct lookup
        if estado_upper in self.ESTADO_INEGI_MAP:
            return self.ESTADO_INEGI_MAP[estado_upper]
        
        # Try removing common prefixes/suffixes
        estado_clean = estado_upper.replace('ESTADO DE ', '').replace('EDO. ', '')
        if estado_clean in self.ESTADO_INEGI_MAP:
            return self.ESTADO_INEGI_MAP[estado_clean]
        
        # Partial match
        for state_name, code in self.ESTADO_INEGI_MAP.items():
            if state_name in estado_upper or estado_upper in state_name:
                return code
        
        logger.warning(f"Could not map state to INEGI code: {estado}")
        return ''
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date to ISO format."""
        # Implementation similar to EC driver
        from datetime import datetime
        
        date_text = date_text.strip()
        
        patterns = [
            (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d')
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    date_obj = datetime.strptime(match.group(0), date_format)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    pass
        
        return None
    
    def _clean_cert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize certificador data."""
        # Remove None values
        cleaned = {k: v for k, v in data.items() if v is not None}
        
        # Ensure required fields
        if 'tipo' in cleaned:
            cleaned['tipo'] = cleaned['tipo'].upper()
        
        # Convert lists to JSON-serializable format
        if 'estandares_acreditados' in cleaned:
            cleaned['estandares_acreditados'] = list(set(cleaned['estandares_acreditados']))
        
        return cleaned
    
    def _create_ec_relationships(self, cert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create EC relationship records."""
        relationships = []
        
        if cert_data.get('estandares_acreditados'):
            for ec_code in cert_data['estandares_acreditados']:
                relationships.append({
                    'type': 'ece_ec_relation',
                    'cert_id': cert_data['cert_id'],
                    'ec_clave': ec_code,
                    'acreditado_desde': cert_data.get('fecha_acreditacion'),
                    'run_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'extracted_at': datetime.now().isoformat()
                })
        
        return relationships
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate certificador item."""
        # Check if it's a relation or main item
        if item.get('type') == 'ece_ec_relation':
            return bool(item.get('cert_id') and item.get('ec_clave'))
        
        # Main certificador validation
        required = ['cert_id', 'tipo', 'nombre_legal', 'src_url']
        
        for field in required:
            if not item.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate type
        if item['tipo'] not in ['ECE', 'OC']:
            logger.warning(f"Invalid certificador type: {item['tipo']}")
            return False
        
        return True
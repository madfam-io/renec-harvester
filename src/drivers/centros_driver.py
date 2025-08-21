"""
Centros (Evaluation Centers) driver for RENEC data extraction.
"""
import re
import json
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime
import logging

from scrapy.http import Response
from scrapy import Request

from .base_driver import BaseDriver
from .certificadores_driver import CertificadoresDriver

logger = logging.getLogger(__name__)


class CentrosDriver(BaseDriver):
    """Driver for extracting Evaluation Centers (Centros de Evaluación) data."""
    
    # RENEC endpoints for centers
    CENTRO_ENDPOINTS = {
        'list': '/RENEC/controlador.do?comp=CENTROS',
        'by_cert': '/RENEC/controlador.do?comp=CERT_CENTROS&id={}',
        'detail': '/RENEC/controlador.do?comp=CENTRO&id={}',
        'standards': '/RENEC/controlador.do?comp=CENTRO_EC&id={}'
    }
    
    def __init__(self, spider):
        """Initialize with shared state mapping."""
        super().__init__(spider)
        # Reuse state mapping from certificadores
        self.ESTADO_INEGI_MAP = CertificadoresDriver.ESTADO_INEGI_MAP
    
    def get_start_urls(self) -> List[str]:
        """Get initial URLs for centers extraction."""
        base_url = 'https://conocer.gob.mx'
        
        # Start with main centers listing
        return [base_url + self.CENTRO_ENDPOINTS['list']]
    
    def parse(self, response: Response) -> Generator[Any, None, None]:
        """Parse centers listing page."""
        self.update_stats('pages_processed')
        
        try:
            # Check if this is a certificador-specific listing
            if 'CERT_CENTROS' in response.url:
                cert_id = self._extract_cert_id_from_url(response.url)
                yield from self._parse_cert_centers(response, cert_id)
            else:
                # Main centers listing
                yield from self._parse_main_listing(response)
            
            # Handle pagination
            next_page = self.handle_pagination(response)
            if next_page:
                yield next_page
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def _parse_main_listing(self, response: Response) -> Generator[Any, None, None]:
        """Parse main centers listing."""
        logger.info("Parsing main centers listing")
        
        # Extract center entries
        center_entries = self._extract_center_list(response)
        
        for entry in center_entries:
            # Create detail page request if ID available
            if entry.get('centro_id'):
                detail_url = self._build_detail_url(entry['centro_id'])
                
                yield self.create_request(
                    url=detail_url,
                    callback=self.parse_detail,
                    meta={'center_data': entry},
                    priority=5
                )
            else:
                # If no detail page, yield what we have
                if self.validate_item(entry):
                    self.update_stats('items_extracted')
                    yield entry
    
    def _parse_cert_centers(self, response: Response, cert_id: str) -> Generator[Any, None, None]:
        """Parse centers belonging to a specific certificador."""
        logger.info(f"Parsing centers for certificador: {cert_id}")
        
        center_entries = self._extract_center_list(response)
        
        for entry in center_entries:
            # Add certificador reference
            entry['cert_id'] = cert_id
            
            if entry.get('centro_id'):
                detail_url = self._build_detail_url(entry['centro_id'])
                
                yield self.create_request(
                    url=detail_url,
                    callback=self.parse_detail,
                    meta={'center_data': entry},
                    priority=5
                )
            else:
                if self.validate_item(entry):
                    self.update_stats('items_extracted')
                    yield entry
    
    def parse_detail(self, response: Response) -> Generator[Any, None, None]:
        """Parse center detail page."""
        self.update_stats('pages_processed')
        
        try:
            # Get basic data from listing
            center_data = response.meta.get('center_data', {})
            
            # Extract detailed information
            detail_data = {
                'centro_id': center_data.get('centro_id'),
                'nombre': self._extract_nombre(response),
                'cert_id': center_data.get('cert_id') or self._extract_cert_reference(response),
                'domicilio_texto': self._extract_domicilio(response),
                'estado': self._extract_estado(response),
                'municipio': self._extract_municipio(response),
                'cp': self._extract_cp(response),
                'telefono': self._extract_telefono(response),
                'correo': self._extract_correo(response),
                'responsable': self._extract_responsable(response),
                'fecha_acreditacion': self._extract_fecha_acreditacion(response),
                'modalidades': self._extract_modalidades(response),
                'src_url': response.url,
                'extracted_at': datetime.now().isoformat()
            }
            
            # Normalize state to INEGI code
            if detail_data.get('estado'):
                detail_data['estado_inegi'] = self._normalize_estado_inegi(detail_data['estado'])
            
            # Extract EC standards
            ec_standards = self._extract_ec_standards(response)
            if ec_standards:
                detail_data['estandares_evaluacion'] = ec_standards
            
            # Merge with listing data
            detail_data.update(center_data)
            
            # Clean and validate
            detail_data = self._clean_center_data(detail_data)
            
            # Compute content hash
            detail_data['row_hash'] = self.compute_content_hash(detail_data)
            
            if self.validate_item(detail_data):
                self.update_stats('items_extracted')
                
                # Yield main center item
                yield detail_data
                
                # Yield EC relationships if found
                if detail_data.get('estandares_evaluacion'):
                    for ec_relation in self._create_ec_relationships(detail_data):
                        yield ec_relation
            else:
                logger.warning(f"Invalid center item: {detail_data.get('centro_id')}")
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def _extract_center_list(self, response: Response) -> List[Dict[str, Any]]:
        """Extract center entries from listing page."""
        centers = []
        
        # Try table format first
        rows = response.xpath('//table[@class="table"]//tr[position()>1]')
        
        if rows:
            for row in rows:
                center = self._parse_table_row(row)
                if center:
                    centers.append(center)
        else:
            # Try card/div format
            cards = response.xpath('//div[@class="centro-card"]')
            for card in cards:
                center = self._parse_card_format(card)
                if center:
                    centers.append(center)
        
        # Alternative: Look for links with centro pattern
        if not centers:
            links = response.xpath('//a[contains(@href, "CENTRO") and contains(@href, "id=")]')
            for link in links:
                center_id = self._extract_id_from_link(link.xpath('@href').get())
                if center_id:
                    centers.append({
                        'centro_id': center_id,
                        'nombre': self.clean_text(link.xpath('.//text()').get())
                    })
        
        return centers
    
    def _parse_table_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse center from table row."""
        try:
            # Extract ID from link or data attribute
            centro_link = row.xpath('.//a[contains(@href, "id=")]/@href').get()
            centro_id = None
            
            if centro_link:
                centro_id = self._extract_id_from_link(centro_link)
            
            if not centro_id:
                centro_id = row.xpath('.//@data-centro-id').get()
            
            return {
                'centro_id': centro_id,
                'nombre': self.clean_text(
                    row.xpath('.//td[1]//text()').get()
                ),
                'cert_nombre': self.clean_text(
                    row.xpath('.//td[2]//text()').get()
                ),
                'estado': self.clean_text(
                    row.xpath('.//td[3]//text()').get()
                ),
                'municipio': self.clean_text(
                    row.xpath('.//td[4]//text()').get()
                )
            }
        except Exception as e:
            logger.warning(f"Failed to parse table row: {e}")
            return None
    
    def _parse_card_format(self, card) -> Optional[Dict[str, Any]]:
        """Parse center from card/div format."""
        try:
            centro_id = card.xpath('.//@data-centro-id').get()
            if not centro_id:
                link = card.xpath('.//a[contains(@href, "id=")]/@href').get()
                if link:
                    centro_id = self._extract_id_from_link(link)
            
            return {
                'centro_id': centro_id,
                'nombre': self.clean_text(
                    card.xpath('.//h3[@class="centro-name"]//text()').get()
                ),
                'cert_nombre': self.clean_text(
                    card.xpath('.//span[@class="cert-name"]//text()').get()
                ),
                'estado': self.clean_text(
                    card.xpath('.//span[@class="estado"]//text()').get()
                ),
                'municipio': self.clean_text(
                    card.xpath('.//span[@class="municipio"]//text()').get()
                )
            }
        except Exception as e:
            logger.warning(f"Failed to parse card format: {e}")
            return None
    
    def _extract_id_from_link(self, link: str) -> Optional[str]:
        """Extract center ID from URL."""
        if not link:
            return None
        
        match = re.search(r'id=([^&]+)', link)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_cert_id_from_url(self, url: str) -> Optional[str]:
        """Extract certificador ID from URL."""
        match = re.search(r'id=([^&]+)', url)
        if match:
            return match.group(1)
        return None
    
    def _build_detail_url(self, centro_id: str) -> str:
        """Build detail page URL for center."""
        base_url = 'https://conocer.gob.mx'
        return base_url + self.CENTRO_ENDPOINTS['detail'].format(centro_id)
    
    def _extract_nombre(self, response: Response) -> str:
        """Extract center name."""
        selectors = [
            '//h1[@class="centro-title"]//text()',
            '//td[contains(text(), "Nombre")]/following-sibling::td//text()',
            '//div[@class="nombre-centro"]//text()'
        ]
        
        for selector in selectors:
            nombre = self.extract_text(response, selector)
            if nombre:
                return self.clean_text(nombre)
        
        return ''
    
    def _extract_cert_reference(self, response: Response) -> Optional[str]:
        """Extract certificador reference from detail page."""
        # Look for certificador link or text
        cert_link = response.xpath('//a[contains(@href, "CERT") and contains(@href, "id=")]/@href').get()
        if cert_link:
            return self._extract_id_from_link(cert_link)
        
        # Try text reference
        cert_text = self.extract_text(
            response,
            '//td[contains(text(), "Certificador")]/following-sibling::td//text()'
        )
        
        # Extract ID from text if present
        if cert_text:
            match = re.search(r'\b(ECE|OC)\d+\b', cert_text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_domicilio(self, response: Response) -> str:
        """Extract full address."""
        selectors = [
            '//td[contains(text(), "Domicilio")]/following-sibling::td//text()',
            '//div[@class="domicilio"]//text()',
            '//address//text()'
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
        
        if not estado and response.meta.get('center_data'):
            estado = response.meta['center_data'].get('estado', '')
        
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
        """Extract phone number."""
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
    
    def _extract_responsable(self, response: Response) -> str:
        """Extract responsible person name."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Responsable")]/following-sibling::td//text()'
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
    
    def _extract_modalidades(self, response: Response) -> List[str]:
        """Extract evaluation modalities."""
        modalidades = []
        
        # Look for modalities list
        items = response.xpath(
            '//td[contains(text(), "Modalidad")]/following-sibling::td//li//text()'
        ).getall()
        
        if items:
            modalidades = [self.clean_text(item) for item in items if item.strip()]
        else:
            # Try comma-separated format
            text = self.extract_text(
                response,
                '//td[contains(text(), "Modalidad")]/following-sibling::td//text()'
            )
            if text:
                modalidades = [self.clean_text(m) for m in text.split(',') if m.strip()]
        
        return modalidades
    
    def _extract_ec_standards(self, response: Response) -> List[str]:
        """Extract EC standards the center can evaluate."""
        standards = []
        
        # Look for standards in various formats
        selectors = [
            '//div[@class="estandares"]//span[@class="ec-code"]//text()',
            '//td[contains(text(), "Estándares")]/following-sibling::td//li//text()',
            '//ul[@class="ec-list"]//li//text()'
        ]
        
        for selector in selectors:
            items = response.xpath(selector).getall()
            if items:
                for item in items:
                    # Extract EC codes
                    matches = re.findall(r'EC\d{4}', item)
                    standards.extend(matches)
                break
        
        # Remove duplicates and validate
        standards = list(set(standards))
        return [ec for ec in standards if re.match(r'^EC\d{4}$', ec)]
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize Mexican phone numbers."""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10:
            return f"+52{digits}"
        elif len(digits) == 12 and digits.startswith('52'):
            return f"+{digits}"
        elif len(digits) == 13 and digits.startswith('052'):
            return f"+52{digits[3:]}"
        else:
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
    
    def _clean_center_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize center data."""
        # Remove None values
        cleaned = {k: v for k, v in data.items() if v is not None}
        
        # Convert lists to JSON-serializable format
        if 'modalidades' in cleaned and isinstance(cleaned['modalidades'], list):
            cleaned['modalidades'] = list(set(cleaned['modalidades']))
        
        if 'estandares_evaluacion' in cleaned and isinstance(cleaned['estandares_evaluacion'], list):
            cleaned['estandares_evaluacion'] = sorted(list(set(cleaned['estandares_evaluacion'])))
        
        return cleaned
    
    def _create_ec_relationships(self, center_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create EC relationship records."""
        relationships = []
        
        if center_data.get('estandares_evaluacion'):
            for ec_code in center_data['estandares_evaluacion']:
                relationships.append({
                    'type': 'centro_ec_relation',
                    'centro_id': center_data['centro_id'],
                    'ec_clave': ec_code,
                    'run_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'extracted_at': datetime.now().isoformat()
                })
        
        return relationships
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate center item."""
        # Check if it's a relation or main item
        if item.get('type') == 'centro_ec_relation':
            return bool(item.get('centro_id') and item.get('ec_clave'))
        
        # Main center validation
        required = ['centro_id', 'nombre', 'src_url']
        
        for field in required:
            if not item.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True
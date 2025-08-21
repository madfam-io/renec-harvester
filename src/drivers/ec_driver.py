"""
EC Standards driver for extracting competency standards from RENEC.
"""
import re
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime
import logging

from scrapy.http import Response
from scrapy import Request

from .base_driver import BaseDriver

logger = logging.getLogger(__name__)


class ECStandardsDriver(BaseDriver):
    """Driver for extracting EC (Estándares de Competencia) data."""
    
    # RENEC component endpoints for EC standards
    EC_ENDPOINTS = {
        'active': '/RENEC/controlador.do?comp=ESLACT',
        'inactive': '/RENEC/controlador.do?comp=ESLINACT', 
        'historical': '/RENEC/controlador.do?comp=ESLHIST',
        'new': '/RENEC/controlador.do?comp=ECNew',
        'search': '/RENEC/controlador.do?comp=ES',
        'detail': '/RENEC/controlador.do?comp=EC&ec={}'
    }
    
    def get_start_urls(self) -> List[str]:
        """Get initial URLs for EC standards extraction."""
        base_url = 'https://conocer.gob.mx'
        
        # Start with active, inactive, and historical standards
        return [
            base_url + self.EC_ENDPOINTS['active'],
            base_url + self.EC_ENDPOINTS['inactive'],
            base_url + self.EC_ENDPOINTS['historical']
        ]
    
    def parse(self, response: Response) -> Generator[Any, None, None]:
        """Parse EC listing page and extract standard references."""
        self.update_stats('pages_processed')
        
        try:
            # Determine which type of listing we're parsing
            listing_type = self._determine_listing_type(response.url)
            logger.info(f"Parsing {listing_type} EC standards listing")
            
            # Extract EC standard rows
            ec_rows = response.xpath('//table[@class="table"]//tr[position()>1]')
            
            if not ec_rows:
                # Try alternative selectors
                ec_rows = response.xpath('//div[@class="ec-list"]//div[@class="ec-item"]')
            
            for row in ec_rows:
                ec_data = self._extract_ec_from_row(row, listing_type)
                if ec_data and self._is_valid_ec_code(ec_data.get('ec_clave', '')):
                    # Create request for detail page
                    detail_url = self._build_detail_url(ec_data['ec_clave'])
                    
                    yield self.create_request(
                        url=detail_url,
                        callback=self.parse_detail,
                        meta={
                            'ec_data': ec_data,
                            'listing_type': listing_type
                        },
                        priority=5
                    )
            
            # Handle pagination
            next_page = self.handle_pagination(response)
            if next_page:
                yield next_page
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def parse_detail(self, response: Response) -> Dict[str, Any]:
        """Parse EC detail page for complete information."""
        self.update_stats('pages_processed')
        
        try:
            # Get basic data from listing
            ec_data = response.meta.get('ec_data', {})
            listing_type = response.meta.get('listing_type', 'unknown')
            
            # Extract detailed information
            detail_data = {
                'ec_clave': ec_data.get('ec_clave'),
                'titulo': self._extract_titulo(response),
                'version': self._extract_version(response),
                'vigente': listing_type == 'active',
                'sector': self._extract_sector(response),
                'sector_id': self._extract_sector_id(response),
                'comite': self._extract_comite(response),
                'comite_id': self._extract_comite_id(response),
                'descripcion': self._extract_descripcion(response),
                'competencias': self._extract_competencias(response),
                'nivel': self._extract_nivel(response),
                'duracion_horas': self._extract_duracion(response),
                'tipo_norma': self._extract_tipo_norma(response),
                'fecha_publicacion': self._extract_fecha_publicacion(response),
                'fecha_vigencia': self._extract_fecha_vigencia(response),
                'perfil_evaluador': self._extract_perfil_evaluador(response),
                'criterios_evaluacion': self._extract_criterios(response),
                'renec_url': response.url,
                'extracted_at': datetime.now().isoformat(),
                'content_hash': None  # Will be computed after
            }
            
            # Merge with listing data
            detail_data.update(ec_data)
            
            # Clean and validate
            detail_data = self._clean_ec_data(detail_data)
            
            # Compute content hash
            detail_data['content_hash'] = self.compute_content_hash(detail_data)
            
            if self.validate_item(detail_data):
                self.update_stats('items_extracted')
                yield detail_data
            else:
                logger.warning(f"Invalid EC item: {detail_data.get('ec_clave')}")
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def _determine_listing_type(self, url: str) -> str:
        """Determine type of EC listing from URL."""
        if 'ESLACT' in url:
            return 'active'
        elif 'ESLINACT' in url:
            return 'inactive'
        elif 'ESLHIST' in url:
            return 'historical'
        elif 'ECNew' in url:
            return 'new'
        else:
            return 'unknown'
    
    def _extract_ec_from_row(self, row_selector, listing_type: str) -> Optional[Dict[str, Any]]:
        """Extract EC data from listing row."""
        try:
            # Try table row format first
            ec_code = self.extract_text(row_selector, './/td[1]//text()')
            ec_title = self.extract_text(row_selector, './/td[2]//text()')
            
            if not ec_code:
                # Try alternative format (div-based)
                ec_code = self.extract_text(row_selector, './/span[@class="ec-code"]//text()')
                ec_title = self.extract_text(row_selector, './/span[@class="ec-title"]//text()')
            
            if ec_code and self._is_valid_ec_code(ec_code):
                return {
                    'ec_clave': ec_code.strip(),
                    'titulo': self.clean_text(ec_title),
                    'listing_type': listing_type
                }
            
        except Exception as e:
            logger.warning(f"Failed to extract EC from row: {e}")
        
        return None
    
    def _is_valid_ec_code(self, code: str) -> bool:
        """Validate EC code format (EC####)."""
        if not code:
            return False
        return bool(re.match(r'^EC\d{4}$', code.strip()))
    
    def _build_detail_url(self, ec_code: str) -> str:
        """Build detail page URL for EC standard."""
        base_url = 'https://conocer.gob.mx'
        return base_url + self.EC_ENDPOINTS['detail'].format(ec_code)
    
    def _extract_titulo(self, response: Response) -> str:
        """Extract EC standard title."""
        selectors = [
            '//h1[@class="ec-title"]//text()',
            '//div[@class="titulo-estandar"]//text()',
            '//td[contains(text(), "Título")]/following-sibling::td//text()',
            '//span[@id="titulo"]//text()'
        ]
        
        for selector in selectors:
            titulo = self.extract_text(response, selector)
            if titulo:
                return self.clean_text(titulo)
        
        return ''
    
    def _extract_version(self, response: Response) -> str:
        """Extract EC version."""
        version_text = self.extract_text(
            response,
            '//td[contains(text(), "Versión")]/following-sibling::td//text()'
        )
        
        if not version_text:
            version_text = self.extract_text(response, '//span[@class="version"]//text()')
        
        # Extract version number
        match = re.search(r'(\d+\.?\d*)', version_text)
        return match.group(1) if match else '1.0'
    
    def _extract_sector(self, response: Response) -> str:
        """Extract sector name."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Sector")]/following-sibling::td//text()'
            )
        )
    
    def _extract_sector_id(self, response: Response) -> Optional[str]:
        """Extract sector ID if available."""
        # Look for sector links
        sector_link = response.xpath(
            '//a[contains(@href, "sector=")]/@href'
        ).get()
        
        if sector_link:
            match = re.search(r'sector=(\d+)', sector_link)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_comite(self, response: Response) -> str:
        """Extract committee name."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Comité")]/following-sibling::td//text()'
            )
        )
    
    def _extract_comite_id(self, response: Response) -> Optional[str]:
        """Extract committee ID if available."""
        comite_link = response.xpath(
            '//a[contains(@href, "comite=")]/@href'
        ).get()
        
        if comite_link:
            match = re.search(r'comite=(\d+)', comite_link)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_descripcion(self, response: Response) -> str:
        """Extract EC description."""
        selectors = [
            '//div[@class="descripcion"]//text()',
            '//td[contains(text(), "Descripción")]/following-sibling::td//text()',
            '//div[@id="descripcion"]//text()'
        ]
        
        for selector in selectors:
            texts = response.xpath(selector).getall()
            if texts:
                return self.clean_text(' '.join(texts))
        
        return ''
    
    def _extract_competencias(self, response: Response) -> List[str]:
        """Extract list of competencies."""
        competencias = []
        
        # Try different selector patterns
        selectors = [
            '//ul[@class="competencias"]//li//text()',
            '//div[@class="competencia-item"]//text()',
            '//td[contains(text(), "Elementos")]/following-sibling::td//li//text()'
        ]
        
        for selector in selectors:
            items = self.extract_all_text(response, selector)
            if items:
                competencias.extend([self.clean_text(item) for item in items])
                break
        
        return competencias
    
    def _extract_nivel(self, response: Response) -> str:
        """Extract competency level."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Nivel")]/following-sibling::td//text()'
            )
        )
    
    def _extract_duracion(self, response: Response) -> Optional[int]:
        """Extract duration in hours."""
        duration_text = self.extract_text(
            response,
            '//td[contains(text(), "Duración")]/following-sibling::td//text()'
        )
        
        if duration_text:
            # Extract numeric value
            match = re.search(r'(\d+)', duration_text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_tipo_norma(self, response: Response) -> str:
        """Extract standard type."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Tipo")]/following-sibling::td//text()'
            )
        )
    
    def _extract_fecha_publicacion(self, response: Response) -> Optional[str]:
        """Extract publication date."""
        date_text = self.extract_text(
            response,
            '//td[contains(text(), "Publicación")]/following-sibling::td//text()'
        )
        
        if date_text:
            # Parse date (handle different formats)
            return self._parse_date(date_text)
        
        return None
    
    def _extract_fecha_vigencia(self, response: Response) -> Optional[str]:
        """Extract validity date."""
        date_text = self.extract_text(
            response,
            '//td[contains(text(), "Vigencia")]/following-sibling::td//text()'
        )
        
        if date_text:
            return self._parse_date(date_text)
        
        return None
    
    def _extract_perfil_evaluador(self, response: Response) -> str:
        """Extract evaluator profile requirements."""
        return self.clean_text(
            self.extract_text(
                response,
                '//div[contains(@class, "perfil-evaluador")]//text()'
            )
        )
    
    def _extract_criterios(self, response: Response) -> List[str]:
        """Extract evaluation criteria."""
        return self.extract_all_text(
            response,
            '//div[@class="criterios"]//li//text()'
        )
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date from various formats to ISO format."""
        import re
        from datetime import datetime
        
        date_text = date_text.strip()
        
        # Try different date patterns
        patterns = [
            (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
            (r'(\d{1,2}) de (\w+) de (\d{4})', None)  # Spanish format
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, date_text)
            if match:
                if date_format:
                    try:
                        date_obj = datetime.strptime(match.group(0), date_format)
                        return date_obj.strftime('%Y-%m-%d')
                    except:
                        pass
                else:
                    # Handle Spanish month names
                    day, month, year = match.groups()
                    month_map = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    if month.lower() in month_map:
                        return f"{year}-{month_map[month.lower()]:02d}-{int(day):02d}"
        
        return None
    
    def _clean_ec_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize EC data."""
        # Remove None values
        cleaned = {k: v for k, v in data.items() if v is not None}
        
        # Ensure required fields
        if 'ec_clave' in cleaned:
            cleaned['ec_clave'] = cleaned['ec_clave'].upper().strip()
        
        # Convert lists to JSON-serializable format
        if 'competencias' in cleaned and isinstance(cleaned['competencias'], list):
            cleaned['competencias'] = [c for c in cleaned['competencias'] if c]
        
        if 'criterios_evaluacion' in cleaned and isinstance(cleaned['criterios_evaluacion'], list):
            cleaned['criterios_evaluacion'] = [c for c in cleaned['criterios_evaluacion'] if c]
        
        return cleaned
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate EC standard item."""
        # Required fields
        required = ['ec_clave', 'titulo', 'renec_url']
        
        for field in required:
            if not item.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate EC code format
        if not self._is_valid_ec_code(item['ec_clave']):
            logger.warning(f"Invalid EC code format: {item['ec_clave']}")
            return False
        
        # Validate title length
        if len(item['titulo']) < 10:
            logger.warning(f"Title too short: {item['titulo']}")
            return False
        
        return True
"""
Sectores and Comités driver for RENEC data extraction.
"""
import re
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime
import logging

from scrapy.http import Response
from scrapy import Request

from .base_driver import BaseDriver

logger = logging.getLogger(__name__)


class SectoresComitesDriver(BaseDriver):
    """Driver for extracting Sectors and Committees data."""
    
    # RENEC endpoints
    ENDPOINTS = {
        'sectores': '/RENEC/controlador.do?comp=SECTORES',
        'sector_detail': '/RENEC/controlador.do?comp=SECTOR&id={}',
        'comites': '/RENEC/controlador.do?comp=COMITES',
        'comite_detail': '/RENEC/controlador.do?comp=COMITE&id={}',
        'sector_comites': '/RENEC/controlador.do?comp=SECTOR_COMITES&id={}',
        'comite_standards': '/RENEC/controlador.do?comp=COMITE_EC&id={}'
    }
    
    def get_start_urls(self) -> List[str]:
        """Get initial URLs for sectors and committees extraction."""
        base_url = 'https://conocer.gob.mx'
        
        return [
            base_url + self.ENDPOINTS['sectores'],
            base_url + self.ENDPOINTS['comites']
        ]
    
    def parse(self, response: Response) -> Generator[Any, None, None]:
        """Parse listing page for sectors or committees."""
        self.update_stats('pages_processed')
        
        try:
            if 'SECTORES' in response.url:
                yield from self._parse_sectores_listing(response)
            elif 'COMITES' in response.url:
                yield from self._parse_comites_listing(response)
            elif 'SECTOR_COMITES' in response.url:
                # Committees belonging to a specific sector
                sector_id = self._extract_id_from_url(response.url)
                yield from self._parse_sector_comites(response, sector_id)
            
            # Handle pagination
            next_page = self.handle_pagination(response)
            if next_page:
                yield next_page
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def _parse_sectores_listing(self, response: Response) -> Generator[Any, None, None]:
        """Parse sectors listing page."""
        logger.info("Parsing sectors listing")
        
        # Extract sector entries
        sector_entries = self._extract_sector_list(response)
        
        for entry in sector_entries:
            if entry.get('sector_id'):
                # Create requests for detail page and committees
                detail_url = self._build_sector_detail_url(entry['sector_id'])
                
                yield self.create_request(
                    url=detail_url,
                    callback=self.parse_sector_detail,
                    meta={'sector_data': entry},
                    priority=5
                )
                
                # Also request committees for this sector
                comites_url = self._build_sector_comites_url(entry['sector_id'])
                yield self.create_request(
                    url=comites_url,
                    callback=self.parse,
                    meta={'sector_id': entry['sector_id']},
                    priority=4
                )
            else:
                # Yield basic data if no detail page
                if self.validate_sector(entry):
                    self.update_stats('items_extracted')
                    yield entry
    
    def _parse_comites_listing(self, response: Response) -> Generator[Any, None, None]:
        """Parse committees listing page."""
        logger.info("Parsing committees listing")
        
        # Extract committee entries
        comite_entries = self._extract_comite_list(response)
        
        for entry in comite_entries:
            if entry.get('comite_id'):
                detail_url = self._build_comite_detail_url(entry['comite_id'])
                
                yield self.create_request(
                    url=detail_url,
                    callback=self.parse_comite_detail,
                    meta={'comite_data': entry},
                    priority=5
                )
            else:
                if self.validate_comite(entry):
                    self.update_stats('items_extracted')
                    yield entry
    
    def _parse_sector_comites(self, response: Response, sector_id: str) -> Generator[Any, None, None]:
        """Parse committees belonging to a specific sector."""
        logger.info(f"Parsing committees for sector: {sector_id}")
        
        comite_entries = self._extract_comite_list(response)
        
        for entry in comite_entries:
            # Add sector reference
            entry['sector_id'] = int(sector_id) if sector_id.isdigit() else None
            
            if entry.get('comite_id'):
                detail_url = self._build_comite_detail_url(entry['comite_id'])
                
                yield self.create_request(
                    url=detail_url,
                    callback=self.parse_comite_detail,
                    meta={'comite_data': entry},
                    priority=5
                )
            else:
                if self.validate_comite(entry):
                    self.update_stats('items_extracted')
                    yield entry
    
    def parse_sector_detail(self, response: Response) -> Dict[str, Any]:
        """Parse sector detail page."""
        self.update_stats('pages_processed')
        
        try:
            # Get basic data from listing
            sector_data = response.meta.get('sector_data', {})
            
            # Extract detailed information
            detail_data = {
                'type': 'sector',
                'sector_id': self._ensure_int(sector_data.get('sector_id')),
                'nombre': self._extract_nombre(response),
                'descripcion': self._extract_descripcion(response),
                'num_comites': self._extract_num_comites(response),
                'num_estandares': self._extract_num_estandares(response),
                'fecha_creacion': self._extract_fecha(response, 'Creación'),
                'src_url': response.url,
                'extracted_at': datetime.now().isoformat()
            }
            
            # Merge with listing data
            detail_data.update(sector_data)
            
            # Clean data
            detail_data = self._clean_data(detail_data)
            
            if self.validate_sector(detail_data):
                self.update_stats('items_extracted')
                yield detail_data
            else:
                logger.warning(f"Invalid sector item: {detail_data.get('sector_id')}")
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def parse_comite_detail(self, response: Response) -> Generator[Any, None, None]:
        """Parse committee detail page."""
        self.update_stats('pages_processed')
        
        try:
            # Get basic data from listing
            comite_data = response.meta.get('comite_data', {})
            
            # Extract detailed information
            detail_data = {
                'type': 'comite',
                'comite_id': self._ensure_int(comite_data.get('comite_id')),
                'nombre': self._extract_nombre(response),
                'sector_id': comite_data.get('sector_id') or self._extract_sector_id(response),
                'descripcion': self._extract_descripcion(response),
                'objetivo': self._extract_objetivo(response),
                'num_estandares': self._extract_num_estandares(response),
                'fecha_creacion': self._extract_fecha(response, 'Creación'),
                'fecha_actualizacion': self._extract_fecha(response, 'Actualización'),
                'contacto': self._extract_contacto(response),
                'src_url': response.url,
                'extracted_at': datetime.now().isoformat()
            }
            
            # Extract EC standards associated with this committee
            ec_standards = self._extract_ec_standards(response)
            if ec_standards:
                detail_data['estandares'] = ec_standards
            
            # Merge with listing data
            detail_data.update(comite_data)
            
            # Clean data
            detail_data = self._clean_data(detail_data)
            
            if self.validate_comite(detail_data):
                self.update_stats('items_extracted')
                yield detail_data
                
                # Yield EC-Sector relationships
                if detail_data.get('sector_id') and ec_standards:
                    for ec_code in ec_standards:
                        yield {
                            'type': 'ec_sector_relation',
                            'ec_clave': ec_code,
                            'sector_id': detail_data['sector_id'],
                            'comite_id': detail_data['comite_id'],
                            'extracted_at': datetime.now().isoformat()
                        }
            else:
                logger.warning(f"Invalid committee item: {detail_data.get('comite_id')}")
                
        except Exception as e:
            self.log_extraction_error(response, e)
    
    def _extract_sector_list(self, response: Response) -> List[Dict[str, Any]]:
        """Extract sector entries from listing."""
        sectors = []
        
        # Try table format
        rows = response.xpath('//table[@class="table"]//tr[position()>1]')
        
        if rows:
            for row in rows:
                sector = {
                    'sector_id': self._extract_id_from_row(row),
                    'nombre': self.clean_text(row.xpath('.//td[1]//text()').get()),
                    'num_comites': self._extract_number(row.xpath('.//td[2]//text()').get()),
                    'num_estandares': self._extract_number(row.xpath('.//td[3]//text()').get())
                }
                
                if sector['sector_id']:
                    sectors.append(sector)
        else:
            # Try card format
            cards = response.xpath('//div[contains(@class, "sector-card")]')
            for card in cards:
                sector_id = card.xpath('.//@data-sector-id').get()
                if not sector_id:
                    link = card.xpath('.//a[contains(@href, "id=")]/@href').get()
                    if link:
                        sector_id = self._extract_id_from_url(link)
                
                if sector_id:
                    sectors.append({
                        'sector_id': int(sector_id) if sector_id.isdigit() else None,
                        'nombre': self.clean_text(card.xpath('.//h3//text()').get())
                    })
        
        return sectors
    
    def _extract_comite_list(self, response: Response) -> List[Dict[str, Any]]:
        """Extract committee entries from listing."""
        comites = []
        
        # Try table format
        rows = response.xpath('//table[@class="table"]//tr[position()>1]')
        
        if rows:
            for row in rows:
                comite = {
                    'comite_id': self._extract_id_from_row(row),
                    'nombre': self.clean_text(row.xpath('.//td[1]//text()').get()),
                    'sector_nombre': self.clean_text(row.xpath('.//td[2]//text()').get()),
                    'num_estandares': self._extract_number(row.xpath('.//td[3]//text()').get())
                }
                
                if comite['comite_id']:
                    comites.append(comite)
        else:
            # Try alternative format
            items = response.xpath('//div[contains(@class, "comite-item")]')
            for item in items:
                comite_id = item.xpath('.//@data-comite-id').get()
                if not comite_id:
                    link = item.xpath('.//a[contains(@href, "id=")]/@href').get()
                    if link:
                        comite_id = self._extract_id_from_url(link)
                
                if comite_id:
                    comites.append({
                        'comite_id': int(comite_id) if comite_id.isdigit() else None,
                        'nombre': self.clean_text(item.xpath('.//text()').get())
                    })
        
        return comites
    
    def _extract_id_from_row(self, row) -> Optional[int]:
        """Extract ID from table row."""
        # Try link first
        link = row.xpath('.//a[contains(@href, "id=")]/@href').get()
        if link:
            id_str = self._extract_id_from_url(link)
            if id_str and id_str.isdigit():
                return int(id_str)
        
        # Try data attribute
        id_attr = row.xpath('.//@data-id').get()
        if id_attr and id_attr.isdigit():
            return int(id_attr)
        
        return None
    
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract ID parameter from URL."""
        if not url:
            return None
        
        match = re.search(r'id=([^&]+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_nombre(self, response: Response) -> str:
        """Extract entity name."""
        selectors = [
            '//h1//text()',
            '//td[contains(text(), "Nombre")]/following-sibling::td//text()',
            '//div[@class="entity-name"]//text()'
        ]
        
        for selector in selectors:
            nombre = self.extract_text(response, selector)
            if nombre:
                return self.clean_text(nombre)
        
        return ''
    
    def _extract_descripcion(self, response: Response) -> str:
        """Extract description."""
        selectors = [
            '//div[@class="descripcion"]//text()',
            '//td[contains(text(), "Descripción")]/following-sibling::td//text()',
            '//p[@class="description"]//text()'
        ]
        
        for selector in selectors:
            texts = response.xpath(selector).getall()
            if texts:
                return self.clean_text(' '.join(texts))
        
        return ''
    
    def _extract_objetivo(self, response: Response) -> str:
        """Extract objective (for committees)."""
        return self.clean_text(
            self.extract_text(
                response,
                '//td[contains(text(), "Objetivo")]/following-sibling::td//text()'
            )
        )
    
    def _extract_num_comites(self, response: Response) -> Optional[int]:
        """Extract number of committees."""
        num_text = self.extract_text(
            response,
            '//td[contains(text(), "Comités")]/following-sibling::td//text()'
        )
        return self._extract_number(num_text)
    
    def _extract_num_estandares(self, response: Response) -> Optional[int]:
        """Extract number of standards."""
        num_text = self.extract_text(
            response,
            '//td[contains(text(), "Estándares")]/following-sibling::td//text()'
        )
        return self._extract_number(num_text)
    
    def _extract_sector_id(self, response: Response) -> Optional[int]:
        """Extract sector ID from committee detail page."""
        # Look for sector link
        sector_link = response.xpath(
            '//a[contains(@href, "SECTOR") and contains(@href, "id=")]/@href'
        ).get()
        
        if sector_link:
            id_str = self._extract_id_from_url(sector_link)
            if id_str and id_str.isdigit():
                return int(id_str)
        
        # Try text reference
        sector_text = self.extract_text(
            response,
            '//td[contains(text(), "Sector")]/following-sibling::td//text()'
        )
        
        if sector_text:
            match = re.search(r'\b(\d+)\b', sector_text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_fecha(self, response: Response, tipo: str) -> Optional[str]:
        """Extract date by type."""
        date_text = self.extract_text(
            response,
            f'//td[contains(text(), "{tipo}")]/following-sibling::td//text()'
        )
        
        if date_text:
            return self._parse_date(date_text)
        
        return None
    
    def _extract_contacto(self, response: Response) -> Optional[str]:
        """Extract contact information."""
        contact_info = {}
        
        # Try to extract various contact fields
        email = self.extract_text(
            response,
            '//td[contains(text(), "Correo")]/following-sibling::td//text()'
        )
        if email:
            contact_info['email'] = self.clean_text(email).lower()
        
        phone = self.extract_text(
            response,
            '//td[contains(text(), "Teléfono")]/following-sibling::td//text()'
        )
        if phone:
            contact_info['phone'] = self.clean_text(phone)
        
        return contact_info if contact_info else None
    
    def _extract_ec_standards(self, response: Response) -> List[str]:
        """Extract EC standards associated with committee."""
        standards = []
        
        # Look for standards list
        selectors = [
            '//div[@class="estandares"]//a[contains(@href, "EC")]//text()',
            '//ul[@class="ec-list"]//li//text()',
            '//td[contains(text(), "Estándares")]/following-sibling::td//a//text()'
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
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Extract number from text."""
        if not text:
            return None
        
        # Find first number in text
        match = re.search(r'\d+', text)
        if match:
            return int(match.group(0))
        
        return None
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date to ISO format."""
        from datetime import datetime
        
        date_text = date_text.strip()
        
        patterns = [
            (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
            (r'(\d{4})', '%Y')  # Year only
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
    
    def _ensure_int(self, value: Any) -> Optional[int]:
        """Ensure value is an integer."""
        if value is None:
            return None
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str) and value.isdigit():
            return int(value)
        
        return None
    
    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize data."""
        # Remove None values
        cleaned = {k: v for k, v in data.items() if v is not None}
        
        # Ensure lists are JSON-serializable
        if 'estandares' in cleaned and isinstance(cleaned['estandares'], list):
            cleaned['estandares'] = sorted(list(set(cleaned['estandares'])))
        
        return cleaned
    
    def _build_sector_detail_url(self, sector_id: int) -> str:
        """Build sector detail URL."""
        base_url = 'https://conocer.gob.mx'
        return base_url + self.ENDPOINTS['sector_detail'].format(sector_id)
    
    def _build_sector_comites_url(self, sector_id: int) -> str:
        """Build sector committees URL."""
        base_url = 'https://conocer.gob.mx'
        return base_url + self.ENDPOINTS['sector_comites'].format(sector_id)
    
    def _build_comite_detail_url(self, comite_id: int) -> str:
        """Build committee detail URL."""
        base_url = 'https://conocer.gob.mx'
        return base_url + self.ENDPOINTS['comite_detail'].format(comite_id)
    
    def validate_sector(self, item: Dict[str, Any]) -> bool:
        """Validate sector item."""
        if item.get('type') != 'sector':
            return True  # Not a sector, skip validation
        
        required = ['sector_id', 'nombre']
        
        for field in required:
            if not item.get(field):
                logger.warning(f"Missing required sector field: {field}")
                return False
        
        # Validate ID is numeric
        if not isinstance(item.get('sector_id'), int):
            logger.warning(f"Invalid sector_id type: {type(item.get('sector_id'))}")
            return False
        
        return True
    
    def validate_comite(self, item: Dict[str, Any]) -> bool:
        """Validate committee item."""
        if item.get('type') not in ['comite', None]:
            return True  # Not a committee, skip validation
        
        required = ['comite_id', 'nombre']
        
        for field in required:
            if not item.get(field):
                logger.warning(f"Missing required committee field: {field}")
                return False
        
        # Validate ID is numeric
        if not isinstance(item.get('comite_id'), int):
            logger.warning(f"Invalid comite_id type: {type(item.get('comite_id'))}")
            return False
        
        return True
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate any item type."""
        item_type = item.get('type', '')
        
        if item_type == 'sector':
            return self.validate_sector(item)
        elif item_type == 'comite':
            return self.validate_comite(item)
        elif item_type == 'ec_sector_relation':
            # Validate relationship
            return bool(
                item.get('ec_clave') and 
                item.get('sector_id') and
                re.match(r'^EC\d{4}$', item['ec_clave'])
            )
        
        return True
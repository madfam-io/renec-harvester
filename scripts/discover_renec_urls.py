#!/usr/bin/env python3
"""
RENEC URL Discovery Script

This script attempts to discover the current working URLs for RENEC components
by testing various URL patterns and analyzing the site structure.
"""

import requests
import time
import json
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
import ssl
import warnings

# Disable SSL warnings for testing
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class RenecUrlDiscoverer:
    """Discover current RENEC URLs and endpoints."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # Bypass SSL verification for testing
        self.session.headers.update({
            'User-Agent': 'RENEC-Harvester/0.2.0 URL-Discovery',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
        })
        self.discovered_urls = {}
        
    def test_url(self, url: str, description: str = "") -> Dict:
        """Test a single URL and return status information."""
        try:
            print(f"Testing {description or url}...")
            response = self.session.get(url, timeout=30)
            
            result = {
                'url': url,
                'status_code': response.status_code,
                'accessible': response.status_code < 400,
                'redirect_url': response.url if response.url != url else None,
                'content_length': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'has_renec_content': self._contains_renec_content(response.text),
                'description': description,
            }
            
            if result['accessible']:
                print(f"✅ {description or url} - Status: {response.status_code}")
                if result['redirect_url']:
                    print(f"   Redirected to: {result['redirect_url']}")
                if result['has_renec_content']:
                    print(f"   Contains RENEC content: ✅")
            else:
                print(f"❌ {description or url} - Status: {response.status_code}")
                
            time.sleep(1)  # Be polite
            return result
            
        except Exception as e:
            print(f"❌ {description or url} - Error: {e}")
            return {
                'url': url,
                'status_code': 0,
                'accessible': False,
                'error': str(e),
                'description': description,
            }
    
    def _contains_renec_content(self, content: str) -> bool:
        """Check if content contains RENEC-related terms."""
        renec_terms = [
            'renec', 'estándar de competencia', 'certificador', 
            'organismo evaluador', 'competencia laboral',
            'conocer', 'ec0', 'oec', 'centros de evaluación'
        ]
        content_lower = content.lower()
        return any(term in content_lower for term in renec_terms)
    
    def discover_main_urls(self) -> Dict:
        """Discover main CONOCER/RENEC URLs."""
        print("\n🔍 Discovering main CONOCER/RENEC URLs...\n")
        
        # Test various potential main URLs
        main_urls = [
            ('https://conocer.gob.mx/', 'CONOCER Main Site'),
            ('https://conocer.gob.mx/RENEC/', 'RENEC Direct'),
            ('https://conocer.gob.mx/RENEC/controlador.do?comp=IR', 'RENEC IR Controller (Original)'),
            ('https://conocer.gob.mx/portal-conocer/', 'CONOCER Portal'),
            ('https://conocer.gob.mx/renec/', 'RENEC Lowercase'),
            ('https://www.conocer.gob.mx/', 'CONOCER with www'),
            ('https://www.conocer.gob.mx/RENEC/', 'RENEC with www'),
        ]
        
        results = {}
        for url, description in main_urls:
            result = self.test_url(url, description)
            results[description] = result
            
        return results
    
    def discover_component_urls(self, base_url: str) -> Dict:
        """Discover component-specific URLs from a working base URL."""
        print(f"\n🔍 Discovering component URLs from {base_url}...\n")
        
        # Various URL patterns to try for components
        patterns = [
            # Legacy patterns
            ('controlador.do?comp=EC', 'EC Standards (Legacy)'),
            ('controlador.do?comp=CE', 'Certificadores (Legacy)'),
            ('controlador.do?comp=IR', 'IR Hub (Legacy)'),
            
            # Modern patterns  
            ('estandares-competencia/', 'EC Standards (Modern)'),
            ('certificadores/', 'Certificadores (Modern)'),
            ('organismos-certificadores/', 'OEC (Modern)'),
            ('centros-evaluacion/', 'Evaluation Centers (Modern)'),
            ('busqueda-estandares/', 'EC Search (Modern)'),
            ('directorio-oec/', 'OEC Directory (Modern)'),
            
            # API patterns
            ('api/v1/estandares/', 'API EC Standards'),
            ('api/v1/certificadores/', 'API Certificadores'),
            ('api/v1/centros/', 'API Centers'),
            ('api/estandares/', 'API EC (v2)'),
            ('api/oec/', 'API OEC'),
            
            # Search patterns
            ('busqueda/', 'General Search'),
            ('consulta/', 'General Query'),
            ('directorio/', 'General Directory'),
        ]
        
        results = {}
        for pattern, description in patterns:
            url = urljoin(base_url, pattern)
            result = self.test_url(url, description)
            results[description] = result
            
        return results
    
    def analyze_working_page(self, url: str) -> Dict:
        """Analyze a working page to extract more URLs."""
        print(f"\n🔍 Analyzing working page: {url}...\n")
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code >= 400:
                return {'error': f'Page not accessible: {response.status_code}'}
            
            content = response.text
            analysis = {
                'has_forms': '<form' in content.lower(),
                'has_javascript': '<script' in content.lower(),
                'has_ajax': any(term in content.lower() for term in ['ajax', 'xhr', 'fetch', 'api']),
                'potential_links': self._extract_potential_links(content, url),
            }
            
            print(f"Page analysis:")
            print(f"  Has forms: {analysis['has_forms']}")
            print(f"  Has JavaScript: {analysis['has_javascript']}")
            print(f"  Has AJAX/API calls: {analysis['has_ajax']}")
            print(f"  Potential RENEC links found: {len(analysis['potential_links'])}")
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_potential_links(self, content: str, base_url: str) -> List[str]:
        """Extract potential RENEC-related links from page content."""
        import re
        
        # Find all href attributes
        href_pattern = r'href=["\'](.*?)["\']'
        links = re.findall(href_pattern, content, re.IGNORECASE)
        
        renec_links = []
        renec_terms = ['renec', 'estandar', 'competencia', 'certificador', 'oec', 'controlador']
        
        for link in links:
            if any(term in link.lower() for term in renec_terms):
                absolute_url = urljoin(base_url, link)
                if absolute_url not in renec_links:
                    renec_links.append(absolute_url)
        
        return renec_links[:20]  # Return first 20
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive report of findings."""
        report = []
        report.append("# RENEC URL Discovery Report")
        report.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Working URLs
        working_urls = []
        failed_urls = []
        
        for section, data in results.items():
            if isinstance(data, dict):
                for desc, result in data.items():
                    if result.get('accessible'):
                        working_urls.append((result['url'], desc, result.get('has_renec_content', False)))
                    else:
                        failed_urls.append((result['url'], desc, result.get('status_code', 0)))
        
        report.append("## ✅ Working URLs")
        for url, desc, has_content in working_urls:
            content_indicator = "🎯" if has_content else "📄"
            report.append(f"- {content_indicator} **{desc}**: {url}")
        
        report.append("")
        report.append("## ❌ Failed URLs")
        for url, desc, status in failed_urls:
            report.append(f"- **{desc}** (Status: {status}): {url}")
        
        report.append("")
        report.append("## 📋 Recommendations")
        
        if working_urls:
            renec_urls = [item for item in working_urls if item[2]]  # Has RENEC content
            if renec_urls:
                report.append("### Primary RENEC URLs to use:")
                for url, desc, _ in renec_urls:
                    report.append(f"- {desc}: `{url}`")
            else:
                report.append("### No URLs with confirmed RENEC content found")
                report.append("### Accessible URLs that might contain RENEC data:")
                for url, desc, _ in working_urls:
                    report.append(f"- {desc}: `{url}`")
        else:
            report.append("### No working URLs found - site may be down or blocked")
        
        return "\n".join(report)
    
    def save_results(self, results: Dict, filename: str = "renec_url_discovery.json"):
        """Save results to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to {filename}")


def main():
    """Main discovery process."""
    print("🚀 RENEC URL Discovery Tool")
    print("=" * 50)
    
    discoverer = RenecUrlDiscoverer()
    
    # Step 1: Discover main URLs
    main_results = discoverer.discover_main_urls()
    
    # Step 2: Find a working base URL
    working_base = None
    for desc, result in main_results.items():
        if result.get('accessible'):
            working_base = result.get('redirect_url') or result['url']
            print(f"\n✅ Found working base URL: {working_base}")
            break
    
    all_results = {'main_urls': main_results}
    
    if working_base:
        # Step 3: Discover component URLs
        component_results = discoverer.discover_component_urls(working_base)
        all_results['component_urls'] = component_results
        
        # Step 4: Analyze working page
        analysis = discoverer.analyze_working_page(working_base)
        all_results['page_analysis'] = analysis
    
    # Generate and save report
    report = discoverer.generate_report(all_results)
    print("\n" + report)
    
    discoverer.save_results(all_results)
    
    # Save report
    with open("renec_url_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("📄 Report saved to renec_url_report.md")


if __name__ == "__main__":
    main()
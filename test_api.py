"""
Test script for Sprint 2 API endpoints.
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_ec_standards():
    """Test EC standards endpoints."""
    print("\n=== Testing EC Standards ===")
    
    # List standards
    response = requests.get(f"{BASE_URL}/ec-standards?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ List EC standards: {len(data)} items")
        if data:
            # Get detail for first standard
            ec_clave = data[0]['ec_clave']
            detail_response = requests.get(f"{BASE_URL}/ec-standards/{ec_clave}")
            if detail_response.status_code == 200:
                print(f"✓ Get EC standard detail: {ec_clave}")
            
            # Get certificadores for this standard
            cert_response = requests.get(f"{BASE_URL}/ec-standards/{ec_clave}/certificadores")
            if cert_response.status_code == 200:
                cert_data = cert_response.json()
                print(f"✓ Get certificadores for {ec_clave}: {cert_data['total_certificadores']} found")
    else:
        print(f"✗ Failed to list EC standards: {response.status_code}")

def test_certificadores():
    """Test certificadores endpoints."""
    print("\n=== Testing Certificadores ===")
    
    # List certificadores
    response = requests.get(f"{BASE_URL}/certificadores?limit=5&tipo=ECE")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ List certificadores: {len(data)} items")
        if data:
            # Get detail for first certificador
            cert_id = data[0]['cert_id']
            detail_response = requests.get(f"{BASE_URL}/certificadores/{cert_id}")
            if detail_response.status_code == 200:
                print(f"✓ Get certificador detail: {cert_id}")
            
            # Get standards for this certificador
            standards_response = requests.get(f"{BASE_URL}/certificadores/{cert_id}/ec-standards")
            if standards_response.status_code == 200:
                standards_data = standards_response.json()
                print(f"✓ Get EC standards for {cert_id}: {standards_data['total_standards']} found")
    else:
        print(f"✗ Failed to list certificadores: {response.status_code}")
    
    # Test stats by state
    stats_response = requests.get(f"{BASE_URL}/certificadores/stats/by-state")
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
        print(f"✓ Get certificadores stats by state: {stats_data['national_summary']['total_certificadores']} total")
    else:
        print(f"✗ Failed to get stats: {stats_response.status_code}")

def test_centros():
    """Test centros endpoints."""
    print("\n=== Testing Centros ===")
    
    # List centros
    response = requests.get(f"{BASE_URL}/centros?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ List centros: {len(data)} items")
        if data:
            # Get detail for first centro
            centro_id = data[0]['centro_id']
            detail_response = requests.get(f"{BASE_URL}/centros/{centro_id}")
            if detail_response.status_code == 200:
                print(f"✓ Get centro detail: {centro_id}")
    else:
        print(f"✗ Failed to list centros: {response.status_code}")
    
    # Test nearby search
    nearby_response = requests.get(f"{BASE_URL}/centros/nearby?estado_inegi=09&limit=5")
    if nearby_response.status_code == 200:
        nearby_data = nearby_response.json()
        print(f"✓ Find nearby centros in CDMX: {nearby_data['total_found']} found")
    else:
        print(f"✗ Failed to find nearby centros: {nearby_response.status_code}")

def test_sectores():
    """Test sectores endpoints."""
    print("\n=== Testing Sectores ===")
    
    # List sectores
    response = requests.get(f"{BASE_URL}/sectores?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ List sectores: {len(data)} items")
        if data:
            # Get detail for first sector
            sector_id = data[0]['sector_id']
            detail_response = requests.get(f"{BASE_URL}/sectores/{sector_id}")
            if detail_response.status_code == 200:
                print(f"✓ Get sector detail: {data[0]['nombre']}")
    else:
        print(f"✗ Failed to list sectores: {response.status_code}")
    
    # Test comités
    comites_response = requests.get(f"{BASE_URL}/comites?limit=5")
    if comites_response.status_code == 200:
        comites_data = comites_response.json()
        print(f"✓ List comités: {len(comites_data)} items")
    else:
        print(f"✗ Failed to list comités: {comites_response.status_code}")

def test_search():
    """Test search endpoints."""
    print("\n=== Testing Search ===")
    
    # Test general search
    search_response = requests.get(f"{BASE_URL}/search?q=seguridad&limit=5")
    if search_response.status_code == 200:
        search_data = search_response.json()
        print(f"✓ Search 'seguridad': {search_data['total_results']} results")
    else:
        print(f"✗ Failed to search: {search_response.status_code}")
    
    # Test autocomplete
    suggest_response = requests.get(f"{BASE_URL}/search/suggest?q=EC02&entity_type=ec_standards")
    if suggest_response.status_code == 200:
        suggest_data = suggest_response.json()
        print(f"✓ Autocomplete 'EC02': {len(suggest_data['suggestions'])} suggestions")
    else:
        print(f"✗ Failed to get suggestions: {suggest_response.status_code}")
    
    # Test location search
    location_response = requests.get(f"{BASE_URL}/search/by-location?estado_inegi=09")
    if location_response.status_code == 200:
        location_data = location_response.json()
        print(f"✓ Search by location (CDMX): Found entities")
    else:
        print(f"✗ Failed to search by location: {location_response.status_code}")

def main():
    """Run all API tests."""
    print("Testing RENEC Harvester Sprint 2 API Endpoints")
    print("=" * 50)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code != 200:
            print("✗ API is not running. Start it with: python3 -m src.api.main")
            return
        print("✓ API is running")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Start it with: python3 -m src.api.main")
        return
    
    # Run tests
    test_ec_standards()
    test_certificadores()
    test_centros()
    test_sectores()
    test_search()
    
    print("\n" + "=" * 50)
    print("API testing complete!")

if __name__ == "__main__":
    main()
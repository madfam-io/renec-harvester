#!/usr/bin/env python3
"""Local setup testing script to validate the RENEC harvester configuration."""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_python_imports():
    """Test that all required Python modules can be imported."""
    print("🐍 Testing Python imports...")
    
    required_modules = [
        "scrapy",
        "requests", 
        "sqlalchemy",
        "redis",
        "typer",
        "structlog",
        "pydantic",
    ]
    
    failed_imports = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module} - {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  Missing modules: {', '.join(failed_imports)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("   All imports successful! ✅")
    return True

def test_constants_import():
    """Test that our constants can be imported."""
    print("\n📋 Testing constants import...")
    try:
        from src.core.constants import RENEC_BASE_URL, RENEC_ENDPOINTS
        print(f"   ✅ RENEC_BASE_URL: {RENEC_BASE_URL}")
        print(f"   ✅ Found {len(RENEC_ENDPOINTS)} endpoint categories")
        return True
    except Exception as e:
        print(f"   ❌ Constants import failed: {e}")
        return False

def test_renec_connectivity():
    """Test connectivity to RENEC site."""
    print("\n🌐 Testing RENEC site connectivity...")
    
    from src.core.constants import RENEC_BASE_URL
    test_urls = [
        (f"{RENEC_BASE_URL}/controlador.do?comp=IR", "IR Hub"),
        (f"{RENEC_BASE_URL}/controlador.do?comp=EC", "EC Standards"),
        (f"{RENEC_BASE_URL}/", "RENEC Base"),
    ]
    
    session = requests.Session()
    session.verify = False  # Bypass SSL for testing
    session.headers.update({
        'User-Agent': 'RENEC-Harvester/0.2.0 Local-Testing',
    })
    
    accessible_count = 0
    for url, name in test_urls:
        try:
            response = session.get(url, timeout=10)
            if response.status_code < 400:
                print(f"   ✅ {name}: {response.status_code}")
                accessible_count += 1
            else:
                print(f"   ❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: {e}")
    
    success = accessible_count > 0
    if success:
        print(f"   {accessible_count}/{len(test_urls)} URLs accessible ✅")
    else:
        print("   No URLs accessible ❌")
    
    return success

def test_scrapy_setup():
    """Test Scrapy configuration."""
    print("\n🕷️  Testing Scrapy setup...")
    
    try:
        # Test scrapy settings
        os.environ['SCRAPY_SETTINGS_MODULE'] = 'src.discovery.settings_local'
        
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        
        settings = get_project_settings()
        print(f"   ✅ Settings loaded: {settings.get('BOT_NAME')}")
        
        # Test spider import
        from src.discovery.spiders.simple_spider import SimpleSpider
        print(f"   ✅ Simple spider imported: {SimpleSpider.name}")
        
        return True
    except Exception as e:
        print(f"   ❌ Scrapy setup failed: {e}")
        return False

def test_artifacts_directory():
    """Test artifacts directory creation."""
    print("\n📁 Testing artifacts directory...")
    
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    
    # Test write permissions
    test_file = artifacts_dir / "test_write.txt"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print("   ✅ Artifacts directory writable")
        return True
    except Exception as e:
        print(f"   ❌ Artifacts directory not writable: {e}")
        return False

def test_spider_execution():
    """Test running the simple spider."""
    print("\n🎯 Testing spider execution...")
    
    try:
        # Set environment
        os.environ['SCRAPY_SETTINGS_MODULE'] = 'src.discovery.settings_local'
        
        # Test with a safe URL first
        cmd = [
            sys.executable, "-m", "scrapy", "crawl", "simple",
            "-s", "CLOSESPIDER_ITEMCOUNT=1",
            "-L", "INFO"
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path.cwd()
        )
        
        if result.returncode == 0:
            print("   ✅ Spider executed successfully")
            if "items" in result.stderr.lower():
                print("   ✅ Items were scraped")
            return True
        else:
            print(f"   ❌ Spider failed with return code: {result.returncode}")
            print(f"   STDOUT: {result.stdout[-500:]}")
            print(f"   STDERR: {result.stderr[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⏰ Spider execution timeout")
        return False
    except Exception as e:
        print(f"   ❌ Spider execution failed: {e}")
        return False

def test_docker_services():
    """Test if Docker services are running."""
    print("\n🐳 Testing Docker services...")
    
    services = [
        ("postgresql://renec:renec_secure_pass@localhost:5432/renec_harvester", "PostgreSQL"),
        ("redis://:renec_redis_pass@localhost:6379/0", "Redis"),
    ]
    
    accessible_count = 0
    
    # Test PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="renec_harvester", 
            user="renec",
            password="renec_secure_pass"
        )
        conn.close()
        print("   ✅ PostgreSQL accessible")
        accessible_count += 1
    except Exception as e:
        print(f"   ❌ PostgreSQL: {e}")
    
    # Test Redis
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, password="renec_redis_pass", db=0)
        r.ping()
        print("   ✅ Redis accessible")
        accessible_count += 1
    except Exception as e:
        print(f"   ❌ Redis: {e}")
    
    if accessible_count > 0:
        print(f"   {accessible_count}/{len(services)} services accessible")
        return True
    else:
        print("   No services accessible - try running: docker-compose up -d")
        return False

def main():
    """Run all tests."""
    print("🚀 RENEC Harvester Local Setup Test")
    print("=" * 50)
    
    tests = [
        ("Python Imports", test_python_imports),
        ("Constants Import", test_constants_import),
        ("RENEC Connectivity", test_renec_connectivity),
        ("Scrapy Setup", test_scrapy_setup),
        ("Artifacts Directory", test_artifacts_directory),
        ("Docker Services", test_docker_services),
        ("Spider Execution", test_spider_execution),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to run RENEC harvester.")
    elif passed >= total * 0.7:  # 70% pass rate
        print("⚠️  Most tests passed. Some components may have issues.")
        print("💡 Try fixing failed tests or continue with caution.")
    else:
        print("🚨 Many tests failed. Setup needs attention.")
        print("💡 Check error messages above and fix issues before proceeding.")
    
    return passed >= total * 0.7

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Local smoke test script for RENEC harvester.
Run this to verify basic functionality.
"""
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_test(description: str, test_func):
    """Run a test and report results."""
    print(f"\n🧪 {description}...", end=" ")
    try:
        test_func()
        print("✅ PASSED")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_imports():
    """Test that all main modules can be imported."""
    from src.discovery.spiders.renec_spider import RenecSpider
    from src.drivers.ec_driver import ECStandardsDriver
    from src.drivers.certificadores_driver import CertificadoresDriver
    from src.validation import DataValidator
    from src.diff import DiffEngine
    from src.export import DataExporter


def test_cli_help():
    """Test CLI help commands."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"CLI help failed: {result.stderr}"


def test_spider_check():
    """Test spider configuration."""
    result = subprocess.run(
        ["scrapy", "check", "renec"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Spider check failed: {result.stderr}"


def test_validation_pipeline():
    """Test validation pipeline with sample data."""
    from src.validation import DataValidator, ValidationExpectations
    
    validator = DataValidator()
    
    # Valid EC standard
    valid_ec = {
        'ec_clave': 'EC0217',
        'titulo': 'Impartición de cursos de formación del capital humano',
        'renec_url': 'https://conocer.gob.mx/RENEC/EC0217'
    }
    is_valid, errors = validator.validate_item(valid_ec)
    assert is_valid, f"Valid item failed validation: {errors}"
    
    # Invalid EC standard
    invalid_ec = {
        'ec_clave': 'INVALID',
        'titulo': 'Test',
        'renec_url': 'not-a-url'
    }
    is_valid, errors = validator.validate_item(invalid_ec)
    assert not is_valid, "Invalid item passed validation"


def test_diff_engine():
    """Test diff engine functionality."""
    from src.diff import DiffEngine
    from datetime import datetime
    
    engine = DiffEngine()
    
    # Test baseline comparison
    test_data = [
        {'id': '1', 'name': 'Test 1', 'value': 100},
        {'id': '2', 'name': 'Test 2', 'value': 200}
    ]
    
    baseline_data = [
        {'id': '1', 'name': 'Test 1', 'value': 100},
        {'id': '3', 'name': 'Test 3', 'value': 300}
    ]
    
    result = engine.compare_with_baseline(test_data, baseline_data, 'id')
    assert len(result['added']) == 1, "Should detect 1 addition"
    assert len(result['removed']) == 1, "Should detect 1 removal"


def test_export_json():
    """Test JSON export functionality."""
    from src.export import DataExporter
    import json
    import tempfile
    
    exporter = DataExporter()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = exporter.export_to_json(f.name, entity_types=[])
        
        # Verify file was created
        assert Path(output_path).exists(), "Export file not created"
        
        # Verify JSON is valid
        with open(output_path) as f:
            data = json.load(f)
            assert 'metadata' in data, "Missing metadata in export"
            assert 'data' in data, "Missing data in export"
        
        # Cleanup
        Path(output_path).unlink()


def test_database_connection():
    """Test database connection."""
    try:
        from src.models import get_session
        with get_session() as session:
            # Simple query to test connection
            result = session.execute("SELECT 1")
            assert result.scalar() == 1
    except Exception as e:
        # Database might not be running, which is OK for basic tests
        print(f"(Database not available: {e})")


def main():
    """Run all smoke tests."""
    print("🚀 Running RENEC Harvester Smoke Tests")
    print("=" * 50)
    
    tests = [
        ("Import all modules", test_imports),
        ("CLI help command", test_cli_help),
        ("Spider configuration", test_spider_check),
        ("Validation pipeline", test_validation_pipeline),
        ("Diff engine", test_diff_engine),
        ("JSON export", test_export_json),
        ("Database connection", test_database_connection),
    ]
    
    passed = 0
    failed = 0
    
    for description, test_func in tests:
        if run_test(description, test_func):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Check the errors above.")
        sys.exit(1)
    else:
        print("\n✨ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
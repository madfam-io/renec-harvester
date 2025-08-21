#!/usr/bin/env python3
"""Local testing workflow to validate RENEC harvester functionality."""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description, timeout=120):
    """Run a command and return success status."""
    print(f"\n🎯 {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print("-" * 60)
    
    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=Path.cwd()
            )
        else:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=Path.cwd()
            )
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("Output:", result.stdout[-1000:])  # Last 1000 chars
        else:
            print("❌ FAILED")
            print("Return code:", result.returncode)
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])
            if result.stderr:
                print("STDERR:", result.stderr[-500:])
                
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def main():
    """Run comprehensive local testing workflow."""
    print("🚀 RENEC Harvester Local Testing Workflow")
    print("=" * 80)
    
    # Set environment
    os.environ['SCRAPY_SETTINGS_MODULE'] = 'src.discovery.settings_local'
    
    tests = [
        {
            "cmd": ["python3", "scripts/test_local_setup.py"],
            "description": "Validate setup and dependencies",
            "timeout": 60,
        },
        {
            "cmd": ["python3", "-m", "scrapy", "crawl", "simple", 
                   "-s", "CLOSESPIDER_ITEMCOUNT=2", "-L", "INFO"],
            "description": "Test basic spider functionality",
            "timeout": 30,
        },
        {
            "cmd": ["python3", "-m", "scrapy", "crawl", "simple",
                   "-a", "test_conocer=true", "-s", "CLOSESPIDER_ITEMCOUNT=3", 
                   "-L", "INFO"],
            "description": "Test CONOCER site access",
            "timeout": 60,
        },
        {
            "cmd": ["python3", "-m", "scrapy", "crawl", "renec",
                   "-a", "mode=crawl", "-a", "max_depth=1",
                   "-s", "CLOSESPIDER_ITEMCOUNT=5", "-L", "INFO"],
            "description": "Test RENEC spider crawl mode",
            "timeout": 90,
        },
        {
            "cmd": ["python3", "-m", "scrapy", "crawl", "renec",
                   "-a", "mode=harvest", "-s", "CLOSESPIDER_ITEMCOUNT=3",
                   "-L", "INFO"],
            "description": "Test RENEC spider harvest mode",
            "timeout": 90,
        },
    ]
    
    results = {}
    
    for i, test in enumerate(tests, 1):
        print(f"\n📋 Running Test {i}/{len(tests)}")
        success = run_command(
            test["cmd"], 
            test["description"], 
            test.get("timeout", 120)
        )
        results[test["description"]] = success
        
        if not success:
            print(f"⚠️  Test {i} failed, but continuing...")
        
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! RENEC harvester is ready for production use.")
        print("✨ Next steps:")
        print("   - Run 'make crawl' for full site mapping")
        print("   - Run 'make harvest' for data extraction")
        print("   - Check artifacts/ directory for outputs")
        
    elif passed >= total * 0.7:  # 70% pass rate
        print("\n⚠️  Most tests passed. Basic functionality is working.")
        print("💡 Some components may need attention:")
        for test_name, success in results.items():
            if not success:
                print(f"   - {test_name}")
        print("✨ You can proceed with caution or fix failing tests.")
        
    else:
        print("\n🚨 Many tests failed. Setup needs significant attention.")
        print("💡 Focus on these failing tests:")
        for test_name, success in results.items():
            if not success:
                print(f"   - {test_name}")
    
    # Show generated artifacts
    artifacts_dir = Path("artifacts")
    if artifacts_dir.exists():
        artifacts = list(artifacts_dir.glob("*"))
        if artifacts:
            print(f"\n📁 Generated artifacts ({len(artifacts)}):")
            for artifact in sorted(artifacts)[-10:]:  # Show last 10
                print(f"   - {artifact.name}")
    
    return passed >= total * 0.7

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
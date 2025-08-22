#!/usr/bin/env python3
"""
Test database initialization to verify foreign key fixes.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use PostgreSQL for testing (UUID support)
# If no DATABASE_URL is set, provide a test URL
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://renec:test_password@localhost:5432/renec_test'

try:
    print("Testing database initialization...")
    from src.models.base import init_db
    
    # Initialize database
    init_db()
    
    print("✅ Database initialization successful!")
    print("All foreign key constraints resolved correctly.")
    
    # Note: PostgreSQL tables are not cleaned up in this test
        
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
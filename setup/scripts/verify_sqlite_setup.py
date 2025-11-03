#!/usr/bin/env python3
"""Verify SQLite setup and configuration"""

import sys
import os
from pathlib import Path

# Set demo mode before importing database
os.environ["USE_SQLITE_DEMO"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///data/demo.db"
os.environ["ENABLE_AUDIT_LOGGING"] = "false"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def verify_sqlite_setup():
    """Verify SQLite setup is working correctly"""
    print("\n" + "="*60)
    print("🔍 Verifying SQLite Setup")
    print("="*60 + "\n")
    
    errors = []
    warnings = []
    
    # Check 1: Data directory exists
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Created data directory")
    else:
        print("✅ Data directory exists")
    
    # Check 2: SQLite connection module
    try:
        from backend.database.sqlite_connection import (
            sqlite_engine,
            init_sqlite_db,
            get_sqlite_db,
            DB_PATH
        )
        print(f"✅ SQLite connection module loaded")
        print(f"   Database path: {DB_PATH.absolute()}")
    except Exception as e:
        errors.append(f"Failed to import SQLite connection: {e}")
        print(f"❌ Failed to import SQLite connection: {e}")
        return False
    
    # Check 3: Database auto-switching
    try:
        from backend.database import get_db, engine, init_db
        print(f"✅ Database auto-switching working")
        print(f"   Current engine: {type(engine).__name__}")
        
        if "sqlite" in str(engine.url):
            print("✅ Using SQLite engine")
        else:
            warnings.append("Not using SQLite engine (check USE_SQLITE_DEMO env var)")
            print("⚠️  Not using SQLite engine")
    except Exception as e:
        errors.append(f"Database auto-switching failed: {e}")
        print(f"❌ Database auto-switching failed: {e}")
    
    # Check 4: Test database initialization
    try:
        print("\n→ Testing database initialization...")
        init_sqlite_db()
        print("✅ Database tables created successfully")
    except Exception as e:
        errors.append(f"Database initialization failed: {e}")
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Check 5: Test database connection
    try:
        print("\n→ Testing database connection...")
        from backend.database.sqlite_connection import get_sqlite_session
        from sqlalchemy import text
        
        with get_sqlite_session() as db:
            result = db.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("✅ Database connection working")
            else:
                errors.append("Database connection test returned unexpected result")
                print("❌ Database connection test failed")
    except Exception as e:
        errors.append(f"Database connection failed: {e}")
        print(f"❌ Database connection failed: {e}")
    
    # Check 6: Verify foreign keys enabled
    try:
        print("\n→ Verifying foreign keys...")
        from backend.database.sqlite_connection import sqlite_engine
        from sqlalchemy import text
        
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys")).scalar()
            if result == 1:
                print("✅ Foreign keys enabled")
            else:
                warnings.append("Foreign keys not enabled")
                print("⚠️  Foreign keys not enabled")
    except Exception as e:
        warnings.append(f"Could not verify foreign keys: {e}")
        print(f"⚠️  Could not verify foreign keys: {e}")
    
    # Check 7: Database file permissions
    if DB_PATH.exists():
        if os.access(DB_PATH.parent, os.W_OK):
            print("✅ Database directory is writable")
        else:
            errors.append("Database directory is not writable")
            print("❌ Database directory is not writable")
    
    # Summary
    print("\n" + "="*60)
    if errors:
        print("❌ Setup Verification FAILED")
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Setup Verification PASSED")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
        return True
    print("="*60 + "\n")


if __name__ == "__main__":
    success = verify_sqlite_setup()
    sys.exit(0 if success else 1)


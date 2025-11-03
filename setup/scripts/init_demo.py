#!/usr/bin/env python3
"""Initialize SQLite demo database"""

import sys
import os
from pathlib import Path

# Set demo mode before importing database
os.environ["USE_SQLITE_DEMO"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///data/demo.db"
os.environ["ENABLE_AUDIT_LOGGING"] = "false"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.sqlite_connection import init_sqlite_db, create_demo_data

def main():
    print("\n" + "="*60)
    print("🐅 Tiger ID - Demo Database Setup")
    print("="*60 + "\n")
    
    print("→ Initializing SQLite database...")
    init_sqlite_db()
    
    print("\n→ Creating demo data...")
    create_demo_data()
    
    print("\n" + "="*60)
    print("✅ Demo database ready!")
    print("="*60)
    print("\n🚀 Start demo mode:")
    print("   setup\\windows\\START_DEMO.bat")
    print("\n🔑 Login credentials:")
    print("   admin / admin")
    print("   investigator / demo")
    print()


if __name__ == "__main__":
    main()


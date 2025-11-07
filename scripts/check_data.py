#!/usr/bin/env python3
"""Check database for facilities and tigers"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Use SQLite for production (not PostgreSQL)
os.environ['USE_POSTGRESQL'] = 'false'
os.environ['USE_SQLITE_DEMO'] = 'false'

from backend.database.sqlite_connection import get_sqlite_session
from backend.database.models import Facility, Tiger

def main():
    """Check database for facilities and tigers"""
    with get_sqlite_session() as db:
        facilities = db.query(Facility).all()
        tigers = db.query(Tiger).all()
        
        print(f"Facilities in DB: {len(facilities)}")
        print(f"Tigers in DB: {len(tigers)}")
        
        if facilities:
            print(f"\nFirst facility: {facilities[0].exhibitor_name}")
            print(f"  ID: {facilities[0].facility_id}")
            print(f"  License: {facilities[0].usda_license}")
        
        if tigers:
            print(f"\nFirst tiger: {tigers[0].name}")
            print(f"  ID: {tigers[0].tiger_id}")
            print(f"  Status: {tigers[0].status}")

if __name__ == "__main__":
    main()


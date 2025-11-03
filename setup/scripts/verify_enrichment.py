#!/usr/bin/env python3
"""Verify enrichment results"""

import os
import sys
from pathlib import Path

# Set SQLite demo mode
os.environ['USE_SQLITE_DEMO'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///data/demo.db'

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.sqlite_connection import get_sqlite_session
from backend.database.models import Facility, Tiger
from sqlalchemy import func

with get_sqlite_session() as db:
    fac_count = db.query(func.count(Facility.facility_id)).scalar()
    tiger_count = db.query(func.count(Tiger.tiger_id)).scalar()
    ref_fac_count = db.query(func.count(Facility.facility_id)).filter(
        Facility.is_reference_facility == True
    ).scalar()
    
    print(f"Total Facilities: {fac_count}")
    print(f"Reference Facilities: {ref_fac_count}")
    print(f"Total Tigers: {tiger_count}")


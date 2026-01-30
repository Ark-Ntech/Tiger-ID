"""Manual SQLite schema migration - Add discovery tracking fields"""

import sys
import os
import sqlite3
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force SQLite
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

def migrate_schema():
    """Add discovery tracking columns to SQLite database"""

    db_path = Path("data/production.db")

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("Creating new database with updated schema...")
        # If DB doesn't exist, just create it with new schema
        from backend.database.models import Base
        from backend.database.connection import engine
        Base.metadata.create_all(bind=engine)
        print("[OK] Database created with updated schema")
        return True

    print(f"Migrating existing database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Get existing columns
        cursor.execute("PRAGMA table_info(tigers)")
        tiger_columns = [row[1] for row in cursor.fetchall()]

        cursor.execute("PRAGMA table_info(tiger_images)")
        image_columns = [row[1] for row in cursor.fetchall()]

        cursor.execute("PRAGMA table_info(facilities)")
        facility_columns = [row[1] for row in cursor.fetchall()]

        print(f"\nExisting tigers columns: {', '.join(tiger_columns)}")
        print(f"Existing tiger_images columns: {', '.join(image_columns)}")
        print(f"Existing facilities columns: {', '.join(facility_columns)}")

        # Add columns to tigers table
        if 'is_reference' not in tiger_columns:
            print("\n[1] Adding is_reference to tigers...")
            cursor.execute("ALTER TABLE tigers ADD COLUMN is_reference BOOLEAN NOT NULL DEFAULT 0")
            print("[OK] Added")

        if 'discovered_at' not in tiger_columns:
            print("[2] Adding discovered_at to tigers...")
            cursor.execute("ALTER TABLE tigers ADD COLUMN discovered_at DATETIME")
            print("[OK] Added")

        if 'discovered_by_investigation_id' not in tiger_columns:
            print("[3] Adding discovered_by_investigation_id to tigers...")
            cursor.execute("ALTER TABLE tigers ADD COLUMN discovered_by_investigation_id CHAR(36)")
            print("[OK] Added")

        if 'discovery_confidence' not in tiger_columns:
            print("[4] Adding discovery_confidence to tigers...")
            cursor.execute("ALTER TABLE tigers ADD COLUMN discovery_confidence FLOAT")
            print("[OK] Added")

        # Add columns to tiger_images table
        if 'is_reference' not in image_columns:
            print("[5] Adding is_reference to tiger_images...")
            cursor.execute("ALTER TABLE tiger_images ADD COLUMN is_reference BOOLEAN NOT NULL DEFAULT 0")
            print("[OK] Added")

        if 'discovered_by_investigation_id' not in image_columns:
            print("[6] Adding discovered_by_investigation_id to tiger_images...")
            cursor.execute("ALTER TABLE tiger_images ADD COLUMN discovered_by_investigation_id CHAR(36)")
            print("[OK] Added")

        # Add columns to facilities table
        if 'coordinates' not in facility_columns:
            print("[7] Adding coordinates to facilities...")
            cursor.execute("ALTER TABLE facilities ADD COLUMN coordinates JSON")
            print("[OK] Added")

        if 'discovered_at' not in facility_columns:
            print("[8] Adding discovered_at to facilities...")
            cursor.execute("ALTER TABLE facilities ADD COLUMN discovered_at DATETIME")
            print("[OK] Added")

        if 'discovered_by_investigation_id' not in facility_columns:
            print("[9] Adding discovered_by_investigation_id to facilities...")
            cursor.execute("ALTER TABLE facilities ADD COLUMN discovered_by_investigation_id CHAR(36)")
            print("[OK] Added")

        conn.commit()

        print("\n" + "="*70)
        print("[OK] MIGRATION COMPLETE")
        print("="*70)
        print("\nVerifying new schema...")

        # Verify
        cursor.execute("PRAGMA table_info(tigers)")
        tiger_columns_new = [row[1] for row in cursor.fetchall()]

        cursor.execute("PRAGMA table_info(tiger_images)")
        image_columns_new = [row[1] for row in cursor.fetchall()]

        cursor.execute("PRAGMA table_info(facilities)")
        facility_columns_new = [row[1] for row in cursor.fetchall()]

        print(f"\nTigers table now has {len(tiger_columns_new)} columns")
        print(f"TigerImages table now has {len(image_columns_new)} columns")
        print(f"Facilities table now has {len(facility_columns_new)} columns")

        # Check required fields
        required_tiger = ['is_reference', 'discovered_at', 'discovered_by_investigation_id', 'discovery_confidence']
        required_image = ['is_reference', 'discovered_by_investigation_id']
        required_facility = ['coordinates', 'discovered_at', 'discovered_by_investigation_id']

        tigers_ok = all(f in tiger_columns_new for f in required_tiger)
        images_ok = all(f in image_columns_new for f in required_image)
        facilities_ok = all(f in facility_columns_new for f in required_facility)

        if tigers_ok and images_ok and facilities_ok:
            print("\n[OK] All required fields present!")
            return True
        else:
            print(f"\n[FAIL] Some fields missing: Tigers={tigers_ok}, Images={images_ok}, Facilities={facilities_ok}")
            return False

    except Exception as e:
        print(f"\n[FAIL] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*70)
    print("SQLITE SCHEMA MIGRATION - Add Discovery Tracking")
    print("="*70)

    success = migrate_schema()

    if success:
        print("\n[OK] Database is ready for auto-discovery!")
        sys.exit(0)
    else:
        print("\n[FAIL] Migration failed")
        sys.exit(1)

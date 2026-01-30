"""
Migrate embedding column from 512 to 2048 dimensions

This script:
1. Creates a backup table
2. Creates new table with 2048-dim embeddings
3. Copies data (existing embeddings will be lost due to dimension change)
4. Drops old table
5. Renames new table

Note: Existing embeddings cannot be preserved since dimensions are incompatible.
"""

import sqlite3
from pathlib import Path

db_path = Path("data/production.db")

if not db_path.exists():
    print(f"Database not found: {db_path}")
    exit(1)

print("="*70)
print("MIGRATING EMBEDDING DIMENSION: 512 -> 2048")
print("="*70)
print()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Check current table structure
    print("[1] Checking current table structure...")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tiger_images'")
    current_schema = cursor.fetchone()
    print(f"Current schema: {current_schema[0][:100]}...")
    print()

    # Create backup
    print("[2] Creating backup table...")
    cursor.execute("DROP TABLE IF EXISTS tiger_images_backup_512")
    cursor.execute("""
        CREATE TABLE tiger_images_backup_512 AS
        SELECT * FROM tiger_images
    """)
    backup_count = cursor.execute("SELECT COUNT(*) FROM tiger_images_backup_512").fetchone()[0]
    print(f"Backed up {backup_count} records")
    print()

    # Drop old table
    print("[3] Dropping old table...")
    cursor.execute("DROP TABLE tiger_images")
    print("Old table dropped")
    print()

    # Create new table with 2048-dim embeddings
    print("[4] Creating new table with 2048-dimensional embeddings...")
    cursor.execute("""
        CREATE TABLE tiger_images (
            image_id TEXT PRIMARY KEY NOT NULL,
            tiger_id TEXT,
            image_path VARCHAR(500) NOT NULL,
            thumbnail_path VARCHAR(500),
            embedding BLOB,
            side_view VARCHAR(20),
            pose_keypoints TEXT,
            metadata TEXT,
            quality_score REAL,
            verified BOOLEAN DEFAULT 0,
            is_reference BOOLEAN DEFAULT 0,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY(tiger_id) REFERENCES tigers (tiger_id)
        )
    """)
    print("New table created with 2048-dimensional embedding column")
    print()

    # Copy data (excluding embeddings which are incompatible)
    print("[5] Copying data (embeddings will be NULL)...")
    cursor.execute("""
        INSERT INTO tiger_images (
            image_id, tiger_id, image_path, thumbnail_path,
            side_view, pose_keypoints, metadata, quality_score,
            verified, is_reference, created_at, updated_at
        )
        SELECT
            image_id, tiger_id, image_path, thumbnail_path,
            side_view, pose_keypoints, metadata, quality_score,
            verified, is_reference, created_at, updated_at
        FROM tiger_images_backup_512
    """)
    migrated_count = cursor.execute("SELECT COUNT(*) FROM tiger_images").fetchone()[0]
    print(f"Migrated {migrated_count} records (embeddings set to NULL)")
    print()

    # Commit changes
    conn.commit()
    print("✅ Migration complete!")
    print()
    print("Summary:")
    print(f"  - Backup table: tiger_images_backup_512 ({backup_count} records)")
    print(f"  - New table: tiger_images ({migrated_count} records)")
    print(f"  - Embedding dimension: 2048")
    print(f"  - Note: All embeddings are NULL and need to be regenerated")

except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    raise

finally:
    conn.close()

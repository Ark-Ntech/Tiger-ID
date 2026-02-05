"""
Migration 007: Auto-discovery Integration Fields

Adds source tracking columns to investigations and verification_queue tables
to support the auto-discovery pipeline integration.

New fields:
    investigations:
        - source: "user_upload" or "auto_discovery"
        - source_tiger_id: Tiger ID that triggered auto-investigation
        - source_image_id: Image ID that triggered auto-investigation

    verification_queue:
        - source: "auto_discovery" or "user_upload"
        - investigation_id: Source investigation reference

This migration is idempotent and safe to run multiple times.
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> list[str]:
    """Get list of column names for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def get_table_indexes(cursor: sqlite3.Cursor, table_name: str) -> list[str]:
    """Get list of index names for a table."""
    cursor.execute(f"PRAGMA index_list({table_name})")
    return [row[1] for row in cursor.fetchall()]


def add_column_if_not_exists(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
    column_def: str,
    existing_columns: list[str],
) -> bool:
    """Add a column to a table if it doesn't already exist.

    Args:
        cursor: SQLite cursor
        table_name: Name of the table
        column_name: Name of the column to add
        column_def: Column definition (e.g., "VARCHAR(50) DEFAULT 'user_upload'")
        existing_columns: List of existing column names

    Returns:
        True if column was added, False if it already existed
    """
    if column_name in existing_columns:
        print(f"  [SKIP] {table_name}.{column_name} already exists")
        return False

    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
    cursor.execute(sql)
    print(f"  [ADD]  {table_name}.{column_name}")
    return True


def create_index_if_not_exists(
    cursor: sqlite3.Cursor,
    index_name: str,
    table_name: str,
    columns: str,
) -> bool:
    """Create an index if it doesn't already exist.

    Args:
        cursor: SQLite cursor
        index_name: Name of the index
        table_name: Name of the table
        columns: Column(s) to index (e.g., "source" or "source, created_at")

    Returns:
        True if index was created, False if it already existed
    """
    # SQLite supports IF NOT EXISTS for indexes
    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})"
    cursor.execute(sql)
    print(f"  [IDX]  {index_name} on {table_name}({columns})")
    return True


def migrate(db_path: str | Path | None = None) -> bool:
    """Run the migration.

    Args:
        db_path: Path to SQLite database. If None, uses DATABASE_URL env var
                 or defaults to data/tiger_id.db

    Returns:
        True if migration succeeded, False otherwise
    """
    # Determine database path
    if db_path is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/tiger_id.db")
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
        else:
            db_path = "data/tiger_id.db"

    db_path = Path(db_path)

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        print("        Run 'python -c \"from backend.database import init_db; init_db()\"' first")
        return False

    print("=" * 70)
    print("MIGRATION 007: Auto-discovery Integration")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Started:  {datetime.now().isoformat()}")
    print()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # ====================================================================
        # INVESTIGATIONS TABLE
        # ====================================================================
        print("[1/2] Updating investigations table...")

        inv_columns = get_table_columns(cursor, "investigations")
        print(f"      Current columns: {len(inv_columns)}")

        # Add source column
        add_column_if_not_exists(
            cursor,
            "investigations",
            "source",
            "VARCHAR(50) DEFAULT 'user_upload'",
            inv_columns,
        )

        # Add source_tiger_id column
        add_column_if_not_exists(
            cursor,
            "investigations",
            "source_tiger_id",
            "VARCHAR(36)",
            inv_columns,
        )

        # Add source_image_id column
        add_column_if_not_exists(
            cursor,
            "investigations",
            "source_image_id",
            "VARCHAR(36)",
            inv_columns,
        )

        # Create indexes for investigations
        create_index_if_not_exists(
            cursor,
            "idx_investigations_source",
            "investigations",
            "source",
        )
        create_index_if_not_exists(
            cursor,
            "idx_investigations_source_tiger_id",
            "investigations",
            "source_tiger_id",
        )
        create_index_if_not_exists(
            cursor,
            "idx_investigations_source_image_id",
            "investigations",
            "source_image_id",
        )

        print()

        # ====================================================================
        # VERIFICATION_QUEUE TABLE
        # ====================================================================
        print("[2/2] Updating verification_queue table...")

        vq_columns = get_table_columns(cursor, "verification_queue")
        print(f"      Current columns: {len(vq_columns)}")

        # Add source column
        add_column_if_not_exists(
            cursor,
            "verification_queue",
            "source",
            "VARCHAR(50)",
            vq_columns,
        )

        # Add investigation_id column
        add_column_if_not_exists(
            cursor,
            "verification_queue",
            "investigation_id",
            "VARCHAR(36) REFERENCES investigations(investigation_id)",
            vq_columns,
        )

        # Create indexes for verification_queue
        create_index_if_not_exists(
            cursor,
            "idx_verification_queue_source",
            "verification_queue",
            "source",
        )
        create_index_if_not_exists(
            cursor,
            "idx_verification_queue_investigation_id",
            "verification_queue",
            "investigation_id",
        )

        # ====================================================================
        # COMMIT
        # ====================================================================
        conn.commit()

        print()
        print("=" * 70)
        print("[OK] MIGRATION COMPLETE")
        print("=" * 70)

        # Verify migration
        print("\nVerification:")

        inv_columns_new = get_table_columns(cursor, "investigations")
        vq_columns_new = get_table_columns(cursor, "verification_queue")

        required_inv = ["source", "source_tiger_id", "source_image_id"]
        required_vq = ["source", "investigation_id"]

        inv_ok = all(c in inv_columns_new for c in required_inv)
        vq_ok = all(c in vq_columns_new for c in required_vq)

        print(f"  investigations: {len(inv_columns_new)} columns, required fields: {'OK' if inv_ok else 'MISSING'}")
        print(f"  verification_queue: {len(vq_columns_new)} columns, required fields: {'OK' if vq_ok else 'MISSING'}")

        if inv_ok and vq_ok:
            print("\n[OK] All required fields present!")
            return True
        else:
            print("\n[WARN] Some required fields may be missing")
            return False

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify(db_path: str | Path | None = None) -> dict:
    """Verify that the migration has been applied.

    Args:
        db_path: Path to SQLite database

    Returns:
        Dictionary with verification results
    """
    # Determine database path
    if db_path is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/tiger_id.db")
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
        else:
            db_path = "data/tiger_id.db"

    db_path = Path(db_path)

    if not db_path.exists():
        return {"error": f"Database not found: {db_path}"}

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        inv_columns = get_table_columns(cursor, "investigations")
        vq_columns = get_table_columns(cursor, "verification_queue")

        required_inv = ["source", "source_tiger_id", "source_image_id"]
        required_vq = ["source", "investigation_id"]

        return {
            "database": str(db_path),
            "investigations": {
                "columns": inv_columns,
                "required_fields_present": all(c in inv_columns for c in required_inv),
                "has_source": "source" in inv_columns,
                "has_source_tiger_id": "source_tiger_id" in inv_columns,
                "has_source_image_id": "source_image_id" in inv_columns,
            },
            "verification_queue": {
                "columns": vq_columns,
                "required_fields_present": all(c in vq_columns for c in required_vq),
                "has_source": "source" in vq_columns,
                "has_investigation_id": "investigation_id" in vq_columns,
            },
        }
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migration 007: Auto-discovery Integration")
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to SQLite database (default: uses DATABASE_URL or data/tiger_id.db)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify migration status, don't run migration",
    )

    args = parser.parse_args()

    if args.verify:
        result = verify(args.db)
        import json
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("investigations", {}).get("required_fields_present") else 1)
    else:
        success = migrate(args.db)
        sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Initialize database with tables and indexes"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Use SQLite for production (not PostgreSQL)
os.environ['USE_POSTGRESQL'] = 'false'
os.environ['USE_SQLITE_DEMO'] = 'false'

from backend.database import init_db, get_db_session, engine
from backend.database.vector_search import create_vector_index
from backend.database.sqlite_connection import get_sqlite_session
from backend.database.models import User, UserRole
from backend.auth.auth import hash_password
import uuid

def main():
    """Initialize database"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize database')
    parser.add_argument('--ingest-datasets', action='store_true', 
                       help='Ingest datasets after initialization')
    parser.add_argument('--ingest-datasets-dry-run', action='store_true',
                       help='Dry run for dataset ingestion (no changes)')
    
    args = parser.parse_args()
    
    print("Initializing database...")
    
    # Create all tables
    init_db()
    print("[OK] Created all tables")
    
    # Create vector indexes (for SQLite, embeddings are stored as JSON)
    # Note: SQLite doesn't support pgvector, so embeddings are stored as JSONB-like structures
    try:
        with get_db_session() as session:
            # For SQLite, we don't need vector indexes in the same way
            # Embeddings are stored in the database but indexed differently
            print("[OK] Database ready (SQLite mode - embeddings stored as JSON)")
    except Exception as e:
        print(f"WARNING: Could not verify database: {e}")
    
    # Create admin user if it doesn't exist
    print("\nCreating admin user...")
    try:
        with get_sqlite_session() as db:
            existing = db.query(User).filter(User.username == "admin").first()
            if existing:
                print("[OK] Admin user already exists")
            else:
                admin = User(
                    user_id=uuid.uuid4(),
                    username="admin",
                    email="admin@tigerid.local",
                    password_hash=hash_password("admin"),
                    role=UserRole.admin,
                    permissions={
                        "investigations": ["create", "read", "update", "delete"],
                        "tigers": ["create", "read", "update", "delete"],
                        "facilities": ["create", "read", "update", "delete"],
                        "users": ["create", "read", "update", "delete"],
                    },
                    is_active=True,
                    mfa_enabled=False
                )
                db.add(admin)
                db.commit()
                print("[OK] Admin user created (username: admin, password: admin)")
    except Exception as e:
        print(f"WARNING: Could not create admin user: {e}")
    
    # Load data from data/models if database is empty
    print("\nChecking if data needs to be loaded...")
    try:
        with get_sqlite_session() as db:
            from backend.database.models import Facility, Tiger
            facility_count = db.query(Facility).count()
            tiger_count = db.query(Tiger).count()
            
            if facility_count == 0 or tiger_count == 0:
                print("Database is empty, loading data from data/models...")
                load_data_from_models()
            else:
                print(f"[OK] Database already has {facility_count} facilities and {tiger_count} tigers")
    except Exception as e:
        print(f"WARNING: Could not check/load data: {e}")
    
    print("\n[OK] Database initialization complete!")


def load_data_from_models():
    """Load facilities and tigers from data/models directory"""
    from pathlib import Path
    import subprocess
    import sys
    
    project_root = Path(__file__).parent.parent
    
    # Load facilities from Excel file
    excel_file = project_root / "data" / "models" / "2025_10_31 TPC_Tigers non-accredited facilities.xlsx"
    if not excel_file.exists():
        excel_file = project_root / "data" / "models" / "2025_11_09_Hackathon Volunteer Agreement.pdf"
        # Try to find any Excel file in data/models
        excel_files = list(project_root.glob("data/models/*.xlsx"))
        if excel_files:
            excel_file = excel_files[0]
    
    if excel_file.exists() and excel_file.suffix == '.xlsx':
        print(f"Loading facilities from: {excel_file.name}")
        try:
            from scripts.populate_production_db import populate_facilities_from_excel
            from backend.database.sqlite_connection import get_sqlite_session
            with get_sqlite_session() as db:
                stats = populate_facilities_from_excel(excel_file, db)
                print(f"[OK] Loaded {stats['facilities_created']} facilities, {stats['facilities_updated']} updated")
        except Exception as e:
            print(f"WARNING: Could not load facilities: {e}")
    else:
        print(f"WARNING: Excel file not found: {excel_file}")
    
    # Load ATRW tiger images
    atrw_path = project_root / "data" / "models" / "atrw" / "images" / "Amur Tigers"
    if atrw_path.exists():
        print("Loading ATRW tiger images...")
        try:
            # Use the ingest_atrw script
            script_path = project_root / "scripts" / "ingest_atrw.py"
            if script_path.exists():
                import asyncio
                from scripts.ingest_atrw import ingest_atrw_dataset
                asyncio.run(ingest_atrw_dataset(dry_run=False, max_images=None))
                print("[OK] ATRW tiger images loaded")
            else:
                print("WARNING: ingest_atrw.py script not found")
        except Exception as e:
            print(f"WARNING: Could not load ATRW images: {e}")
    else:
        print(f"WARNING: ATRW dataset not found at: {atrw_path}")


def main():
    """Initialize database"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize database')
    parser.add_argument('--ingest-datasets', action='store_true', 
                       help='Ingest datasets after initialization')
    parser.add_argument('--ingest-datasets-dry-run', action='store_true',
                       help='Dry run for dataset ingestion (no changes)')
    
    args = parser.parse_args()
    
    print("Initializing database...")
    
    # Create all tables
    init_db()
    print("[OK] Created all tables")
    
    # Create vector indexes (for SQLite, embeddings are stored as JSON)
    # Note: SQLite doesn't support pgvector, so embeddings are stored as JSONB-like structures
    try:
        with get_db_session() as session:
            # For SQLite, we don't need vector indexes in the same way
            # Embeddings are stored in the database but indexed differently
            print("[OK] Database ready (SQLite mode - embeddings stored as JSON)")
    except Exception as e:
        print(f"WARNING: Could not verify database: {e}")
    
    # Create admin user if it doesn't exist
    print("\nCreating admin user...")
    try:
        with get_sqlite_session() as db:
            existing = db.query(User).filter(User.username == "admin").first()
            if existing:
                print("[OK] Admin user already exists")
            else:
                admin = User(
                    user_id=uuid.uuid4(),
                    username="admin",
                    email="admin@tigerid.local",
                    password_hash=hash_password("admin"),
                    role=UserRole.admin,
                    permissions={
                        "investigations": ["create", "read", "update", "delete"],
                        "tigers": ["create", "read", "update", "delete"],
                        "facilities": ["create", "read", "update", "delete"],
                        "users": ["create", "read", "update", "delete"],
                    },
                    is_active=True,
                    mfa_enabled=False
                )
                db.add(admin)
                db.commit()
                print("[OK] Admin user created (username: admin, password: admin)")
    except Exception as e:
        print(f"WARNING: Could not create admin user: {e}")
    
    # Load data from data/models if database is empty
    print("\nChecking if data needs to be loaded...")
    try:
        with get_sqlite_session() as db:
            from backend.database.models import Facility, Tiger
            facility_count = db.query(Facility).count()
            tiger_count = db.query(Tiger).count()
            
            if facility_count == 0 or tiger_count == 0:
                print("Database is empty, loading data from data/models...")
                load_data_from_models()
            else:
                print(f"[OK] Database already has {facility_count} facilities and {tiger_count} tigers")
    except Exception as e:
        print(f"WARNING: Could not check/load data: {e}")
    
    print("\n[OK] Database initialization complete!")
    
    # Optionally ingest datasets
    if args.ingest_datasets:
        print("\nIngesting datasets...")
        import asyncio
        from scripts.ingest_datasets import DatasetIngester
        
        ingester = DatasetIngester(dry_run=args.ingest_datasets_dry_run)
        results = asyncio.run(ingester.ingest_all_datasets())
        
        stats = ingester.get_stats()
        print(f"\n[OK] Dataset ingestion complete!")
        print(f"  Tigers created: {stats['tigers_created']}")
        print(f"  Images processed: {stats['images_processed']}")


if __name__ == "__main__":
    main()


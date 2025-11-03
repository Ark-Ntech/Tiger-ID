#!/usr/bin/env python3
"""Initialize database with tables and indexes"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database.connection import init_db, engine
from backend.database.vector_search import create_vector_index
from backend.database.connection import get_db_session

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
    print("✓ Created all tables")
    
    # Create vector indexes
    with get_db_session() as session:
        try:
            create_vector_index(session, "tiger_images", "embedding")
            print("✓ Created vector indexes")
        except Exception as e:
            print(f"⚠ Warning: Could not create vector index: {e}")
            print("  This might be normal if pgvector extension is not available")
    
    print("\n✓ Database initialization complete!")
    
    # Optionally ingest datasets
    if args.ingest_datasets:
        print("\nIngesting datasets...")
        import asyncio
        from scripts.ingest_datasets import DatasetIngester
        
        ingester = DatasetIngester(dry_run=args.ingest_datasets_dry_run)
        results = asyncio.run(ingester.ingest_all_datasets())
        
        stats = ingester.get_stats()
        print(f"\n✓ Dataset ingestion complete!")
        print(f"  Tigers created: {stats['tigers_created']}")
        print(f"  Images processed: {stats['images_processed']}")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Validate production database data integrity.

This script verifies that:
1. All facilities from Excel are in database
2. Tiger images are properly linked
3. Embeddings are generated
4. Facility-tiger relationships are correct
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set SQLite production mode
os.environ['USE_SQLITE_DEMO'] = 'false'
os.environ['USE_POSTGRESQL'] = 'false'
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

from backend.database.sqlite_connection import get_sqlite_session
from backend.database.models import Facility, Tiger, TigerImage
from scripts.parse_tpc_facilities_excel import parse_excel_file
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def validate_facilities(excel_path: Path, db_session) -> Dict[str, Any]:
    """Validate that all facilities from Excel are in database"""
    logger.info("Validating facilities from Excel file")
    
    # Parse Excel file
    facilities_data = parse_excel_file(excel_path)
    
    # Get facilities from database
    db_facilities = db_session.query(Facility).all()
    db_facility_map = {}
    for fac in db_facilities:
        key = fac.exhibitor_name.lower().strip()
        if fac.usda_license:
            db_facility_map[fac.usda_license] = fac
        db_facility_map[key] = fac
    
    # Check for missing facilities
    missing_facilities = []
    for facility_data in facilities_data:
        exhibitor_name = facility_data['exhibitor_name'].lower().strip()
        usda_license = facility_data.get('usda_license')
        
        found = False
        if usda_license and usda_license in db_facility_map:
            found = True
        elif exhibitor_name in db_facility_map:
            found = True
        
        if not found:
            missing_facilities.append(facility_data)
    
    stats = {
        'excel_facilities': len(facilities_data),
        'db_facilities': len(db_facilities),
        'missing_facilities': len(missing_facilities),
        'missing_list': missing_facilities[:10]  # First 10
    }
    
    return stats


def validate_tiger_images(db_session) -> Dict[str, Any]:
    """Validate tiger images are properly linked"""
    logger.info("Validating tiger images")
    
    # Get all tigers
    tigers = db_session.query(Tiger).all()
    
    # Get all images
    images = db_session.query(TigerImage).all()
    
    # Check for tigers without images
    tigers_without_images = []
    for tiger in tigers:
        tiger_images = [img for img in images if img.tiger_id == tiger.tiger_id]
        if len(tiger_images) == 0:
            tigers_without_images.append(tiger)
    
    # Check for images without embeddings
    images_without_embeddings = []
    for image in images:
        # Check if embedding exists (stored as JSON in SQLite)
        if not image.embedding:
            images_without_embeddings.append(image)
    
    stats = {
        'total_tigers': len(tigers),
        'total_images': len(images),
        'tigers_without_images': len(tigers_without_images),
        'images_without_embeddings': len(images_without_embeddings),
        'avg_images_per_tiger': len(images) / len(tigers) if tigers else 0
    }
    
    return stats


def validate_facility_tiger_relationships(db_session) -> Dict[str, Any]:
    """Validate facility-tiger relationships"""
    logger.info("Validating facility-tiger relationships")
    
    # Get all facilities
    facilities = db_session.query(Facility).all()
    
    # Get all tigers
    tigers = db_session.query(Tiger).all()
    
    # Check facilities with tigers
    facilities_with_tigers = []
    facilities_without_tigers = []
    
    for facility in facilities:
        facility_tigers = [t for t in tigers if t.origin_facility_id == facility.facility_id]
        if len(facility_tigers) > 0:
            facilities_with_tigers.append({
                'facility': facility.exhibitor_name,
                'tiger_count': len(facility_tigers),
                'expected_count': facility.tiger_count or 0
            })
        else:
            facilities_without_tigers.append(facility.exhibitor_name)
    
    stats = {
        'total_facilities': len(facilities),
        'facilities_with_tigers': len(facilities_with_tigers),
        'facilities_without_tigers': len(facilities_without_tigers),
        'total_tigers': len(tigers),
        'tigers_with_facilities': len([t for t in tigers if t.origin_facility_id]),
        'tigers_without_facilities': len([t for t in tigers if not t.origin_facility_id])
    }
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate production database data')
    parser.add_argument('--excel-file', type=str,
                       default='data/datasets/2025_10_31 TPC_Tigers non-accredited facilities.xlsx',
                       help='Path to Excel file')
    
    args = parser.parse_args()
    
    excel_path = Path(args.excel_file)
    
    print("=" * 60)
    print("Production Database Validation")
    print("=" * 60)
    print()
    
    with get_sqlite_session() as db_session:
        # Validate facilities
        if excel_path.exists():
            print("→ Validating facilities...")
            facility_stats = validate_facilities(excel_path, db_session)
            print(f"  Excel facilities: {facility_stats['excel_facilities']}")
            print(f"  Database facilities: {facility_stats['db_facilities']}")
            print(f"  Missing facilities: {facility_stats['missing_facilities']}")
            if facility_stats['missing_facilities'] > 0:
                print(f"  ⚠ First few missing: {[f['exhibitor_name'] for f in facility_stats['missing_list']]}")
            print()
        else:
            print(f"⚠ Excel file not found: {excel_path}")
            print()
        
        # Validate tiger images
        print("→ Validating tiger images...")
        image_stats = validate_tiger_images(db_session)
        print(f"  Total tigers: {image_stats['total_tigers']}")
        print(f"  Total images: {image_stats['total_images']}")
        print(f"  Tigers without images: {image_stats['tigers_without_images']}")
        print(f"  Images without embeddings: {image_stats['images_without_embeddings']}")
        print(f"  Avg images per tiger: {image_stats['avg_images_per_tiger']:.2f}")
        print()
        
        # Validate relationships
        print("→ Validating facility-tiger relationships...")
        relationship_stats = validate_facility_tiger_relationships(db_session)
        print(f"  Total facilities: {relationship_stats['total_facilities']}")
        print(f"  Facilities with tigers: {relationship_stats['facilities_with_tigers']}")
        print(f"  Facilities without tigers: {relationship_stats['facilities_without_tigers']}")
        print(f"  Total tigers: {relationship_stats['total_tigers']}")
        print(f"  Tigers with facilities: {relationship_stats['tigers_with_facilities']}")
        print(f"  Tigers without facilities: {relationship_stats['tigers_without_facilities']}")
        print()
    
    print("=" * 60)
    print("✓ Validation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()


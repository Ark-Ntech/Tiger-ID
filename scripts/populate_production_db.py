#!/usr/bin/env python3
"""
Production database population script.

This script populates the SQLite production database with:
1. Facility data from TPC_Tigers Excel file
2. Tiger images from datasets (ATRW, etc.)
3. Generated embeddings for all images
4. Proper relationships between facilities and tigers
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set SQLite production mode (not demo mode)
os.environ['USE_SQLITE_DEMO'] = 'false'
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

from backend.database.sqlite_connection import (
    get_sqlite_session, init_sqlite_db, sqlite_engine
)
from backend.database.models import (
    User, UserRole, Facility, Tiger, TigerImage, TigerStatus, SideView
)
from backend.database.vector_search import store_embedding
from backend.services.facility_service import FacilityService
from backend.services.tiger_service import TigerService
from backend.auth.auth import hash_password
from backend.models.reid import TigerReIDModel
from backend.utils.logging import get_logger
from scripts.parse_tpc_facilities_excel import parse_excel_file

logger = get_logger(__name__)

# Update SQLite database path for production
from backend.database import sqlite_connection
from sqlalchemy import create_engine

sqlite_connection.DB_PATH = Path("data/production.db")
sqlite_connection.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
sqlite_connection.sqlite_engine = create_engine(
    f"sqlite:///{sqlite_connection.DB_PATH}",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    echo=False
)


def create_admin_user(db_session):
    """Create admin user if it doesn't exist"""
    existing = db_session.query(User).filter(User.username == "admin").first()
    
    if existing:
        logger.info("Admin user already exists")
        return existing
    
    admin = User(
        user_id=uuid4(),
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
    db_session.add(admin)
    db_session.commit()
    logger.info("Created admin user")
    return admin


def populate_facilities_from_excel(excel_path: Path, db_session) -> Dict[str, Any]:
    """Populate facilities from Excel file"""
    logger.info(f"Parsing Excel file: {excel_path}")
    
    # Parse Excel file
    facilities_data = parse_excel_file(excel_path)
    
    logger.info(f"Found {len(facilities_data)} facilities in Excel file")
    
    facility_service = FacilityService(db_session)
    stats = {
        'facilities_created': 0,
        'facilities_updated': 0,
        'facilities_skipped': 0,
        'errors': []
    }
    
    for facility_data in facilities_data:
        try:
            exhibitor_name = facility_data['exhibitor_name']
            usda_license = facility_data.get('usda_license')
            
            # Check if facility exists
            existing_facility = None
            
            if usda_license:
                existing_facility = facility_service.get_facility_by_license(usda_license)
            
            if not existing_facility:
                # Try to find by name
                facilities = facility_service.get_facilities(
                    search_query=exhibitor_name,
                    limit=10
                )
                for fac in facilities:
                    if fac.exhibitor_name.lower() == exhibitor_name.lower():
                        existing_facility = fac
                        break
            
            if existing_facility:
                # Update existing facility
                logger.debug(f"Updating facility: {exhibitor_name}")
                for key, value in facility_data.items():
                    if key != 'facility_id' and hasattr(existing_facility, key):
                        setattr(existing_facility, key, value)
                stats['facilities_updated'] += 1
            else:
                # Create new facility
                logger.debug(f"Creating facility: {exhibitor_name}")
                facility = Facility(
                    facility_id=uuid4(),
                    exhibitor_name=facility_data['exhibitor_name'],
                    usda_license=facility_data.get('usda_license'),
                    state=facility_data.get('state'),
                    city=facility_data.get('city'),
                    address=facility_data.get('address'),
                    tiger_count=facility_data.get('tiger_count', 0),
                    social_media_links=facility_data.get('social_media_links', {}),
                    website=facility_data.get('website'),
                    ir_date=facility_data.get('ir_date'),
                    accreditation_status=facility_data.get('accreditation_status', 'Non-Accredited'),
                    is_reference_facility=facility_data.get('is_reference_facility', True),
                    data_source=facility_data.get('data_source', 'tpc_non_accredited_facilities'),
                    reference_dataset_version=facility_data.get('reference_dataset_version'),
                    reference_metadata=facility_data.get('reference_metadata', {})
                )
                db_session.add(facility)
                stats['facilities_created'] += 1
            
            db_session.commit()
            
        except Exception as e:
            logger.error(f"Error processing facility {facility_data.get('exhibitor_name', 'unknown')}: {e}", exc_info=True)
            stats['errors'].append(str(e))
            db_session.rollback()
    
    logger.info(f"Facilities: {stats['facilities_created']} created, {stats['facilities_updated']} updated")
    return stats


async def populate_tiger_images(db_session) -> Dict[str, Any]:
    """Populate tiger images from datasets"""
    logger.info("Populating tiger images from datasets")
    
    stats = {
        'tigers_created': 0,
        'images_processed': 0,
        'images_skipped': 0,
        'errors': []
    }
    
    # Initialize RE-ID model for generating embeddings
    reid_model = TigerReIDModel()
    try:
        await reid_model.load_model()
        logger.info("RE-ID model loaded for embedding generation")
    except Exception as e:
        logger.warning(f"Could not load RE-ID model: {e}. Images will be added without embeddings.")
        reid_model = None
    
    # Check multiple dataset locations for tiger images
    project_root = Path(__file__).parent.parent
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    # Potential dataset locations
    dataset_locations = [
        project_root / "data" / "models" / "atrw" / "images",  # ATRW dataset
        project_root / "data" / "datasets" / "wildlife-datasets" / "data" / "ATRW" / "images",  # Wildlife datasets ATRW
        project_root / "data" / "datasets" / "wildlife-datasets" / "data" / "WildlifeReID10k" / "images",  # WildlifeReID-10k (has tigers)
    ]
    
    tiger_dirs = []
    dataset_source = None
    atrw_images_dir = None
    
    # Try each location
    for dataset_path in dataset_locations:
        if dataset_path.exists():
            logger.info(f"Checking dataset location: {dataset_path}")
            # Check if it's a directory of tiger subdirectories or a flat structure
            if (dataset_path / "images").exists():
                # Some datasets have an images subdirectory
                check_path = dataset_path / "images"
            else:
                check_path = dataset_path
            
            dirs = [d for d in check_path.iterdir() if d.is_dir()]
            if dirs:
                tiger_dirs = dirs
                dataset_source = check_path.name
                atrw_images_dir = check_path
                logger.info(f"Found {len(tiger_dirs)} tiger directories in {check_path}")
                break
            else:
                # Check for flat structure with CSV files (like individual-animal-reid)
                csv_files = list(check_path.glob("*.csv"))
                if csv_files:
                    logger.info(f"Found CSV files in {check_path}, will use ingest_datasets.py for this location")
                    # Note: CSV-based datasets should use ingest_datasets.py instead
                    # This is a fallback - prefer directory structure
    
    if not tiger_dirs or not atrw_images_dir:
        logger.warning(f"No tiger directories found in any dataset location. Please download ATRW dataset:")
        logger.warning(f"  - ATRW: https://lila.science/datasets/atrw")
        logger.warning(f"  - Kaggle: https://www.kaggle.com/datasets/quadeer15sh/amur-tiger-reidentification")
        logger.warning(f"  - Extract to: {dataset_locations[0]}")
        logger.warning(f"  - Expected structure: {dataset_locations[0]}/tiger_001/image1.jpg, etc.")
        return stats
    
    logger.info(f"Found {len(tiger_dirs)} tiger directories")
    
    # Get all facilities to link tigers
    facilities = db_session.query(Facility).all()
    facility_map = {fac.facility_id: fac for fac in facilities}
    
    for tiger_dir in tiger_dirs:
        try:
            tiger_id_str = tiger_dir.name
            
            # Find existing tiger or create new one
            tiger = db_session.query(Tiger).filter(Tiger.alias == tiger_id_str).first()
            
            if not tiger:
                # Create tiger - try to link to a facility
                origin_facility_id = None
                if facilities:
                    # Link to first facility with tigers
                    for fac in facilities:
                        if fac.tiger_count > 0:
                            origin_facility_id = fac.facility_id
                            break
                
                tiger = Tiger(
                    tiger_id=uuid4(),
                    name=f"Tiger {tiger_id_str}",
                    alias=tiger_id_str,
                    status=TigerStatus.active,
                    origin_facility_id=origin_facility_id,
                    created_at=datetime.utcnow()
                )
                db_session.add(tiger)
                db_session.flush()
                stats['tigers_created'] += 1
            
            # Find image files
            image_files = [
                f for f in tiger_dir.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            ]
            
            for image_file in image_files:
                # Check if image already exists
                existing = db_session.query(TigerImage).filter(
                    TigerImage.image_path == str(image_file)
                ).first()
                
                if existing:
                    stats['images_skipped'] += 1
                    continue
                
                # Generate embedding if model is available
                embedding = None
                if reid_model:
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(image_file)
                        embedding = await reid_model.generate_embedding(img)
                    except Exception as e:
                        logger.warning(f"Could not generate embedding for {image_file}: {e}")
                
                # Create TigerImage record
                tiger_image = TigerImage(
                    image_id=uuid4(),
                    tiger_id=tiger.tiger_id,
                    image_path=str(image_file),
                    side_view=SideView.unknown,
                    meta_data={
                        'dataset': dataset_source or 'ATRW',
                        'tiger_id_dataset': tiger_id_str,
                        'source_path': str(image_file.relative_to(atrw_images_dir))
                    },
                    verified=False,
                    created_at=datetime.utcnow()
                )
                db_session.add(tiger_image)
                db_session.flush()
                
                # Store embedding if available
                if embedding is not None:
                    try:
                        store_embedding(db_session, str(tiger_image.image_id), embedding)
                    except Exception as e:
                        logger.warning(f"Could not store embedding for {image_file}: {e}")
                
                stats['images_processed'] += 1
                
                # Commit periodically
                if stats['images_processed'] % 100 == 0:
                    db_session.commit()
                    logger.info(f"Processed {stats['images_processed']} images...")
            
        except Exception as e:
            logger.error(f"Error processing tiger directory {tiger_dir}: {e}", exc_info=True)
            stats['errors'].append(str(e))
            db_session.rollback()
    
    db_session.commit()
    logger.info(f"Tiger images: {stats['tigers_created']} tigers created, {stats['images_processed']} images processed")
    return stats


def main():
    parser = argparse.ArgumentParser(description='Populate production database')
    parser.add_argument('--excel-file', type=str, 
                       default='data/datasets/2025_10_31 TPC_Tigers non-accredited facilities.xlsx',
                       help='Path to Excel file')
    parser.add_argument('--skip-facilities', action='store_true',
                       help='Skip facility population')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip tiger image population')
    parser.add_argument('--reset-db', action='store_true',
                       help='Reset database before populating')
    
    args = parser.parse_args()
    
    excel_path = Path(args.excel_file)
    
    print("=" * 60)
    print("Production Database Population")
    print("=" * 60)
    print()
    
    # Initialize database
    if args.reset_db:
        print("→ Resetting database...")
        init_sqlite_db()
        print("✓ Database reset complete")
        print()
    
    with get_sqlite_session() as db_session:
        # Create admin user
        print("→ Creating admin user...")
        create_admin_user(db_session)
        print("✓ Admin user ready")
        print()
        
        # Populate facilities from Excel
        if not args.skip_facilities and excel_path.exists():
            print(f"→ Populating facilities from Excel file...")
            facility_stats = populate_facilities_from_excel(excel_path, db_session)
            print(f"✓ Facilities: {facility_stats['facilities_created']} created, "
                  f"{facility_stats['facilities_updated']} updated")
            if facility_stats['errors']:
                print(f"⚠ {len(facility_stats['errors'])} errors occurred")
            print()
        elif not excel_path.exists():
            print(f"⚠ Excel file not found: {excel_path}")
            print()
        
        # Populate tiger images
        if not args.skip_images:
            print("→ Populating tiger images from datasets...")
            image_stats = asyncio.run(populate_tiger_images(db_session))
            print(f"✓ Tiger images: {image_stats['tigers_created']} tigers created, "
                  f"{image_stats['images_processed']} images processed")
            if image_stats['errors']:
                print(f"⚠ {len(image_stats['errors'])} errors occurred")
            print()
    
    print("=" * 60)
    print("✓ Production database population complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()


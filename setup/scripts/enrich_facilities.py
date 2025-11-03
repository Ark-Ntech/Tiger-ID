#!/usr/bin/env python3
"""
Enrich SQLite demo database with facility data from non-accredited facilities dataset
and other available datasets.

This script:
1. Parses the non-accredited facilities tab-separated file
2. Creates/updates Facility records with all available data
3. Optionally creates Tiger records based on tiger counts
4. Enriches with data from other datasets (ATRW, etc.)
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set SQLite demo mode before any database imports
os.environ['USE_SQLITE_DEMO'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///data/demo.db'

from backend.database.sqlite_connection import get_sqlite_session, init_sqlite_db
from backend.database.models import Facility, Tiger, TigerImage, TigerStatus
from backend.services.facility_service import FacilityService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various date formats from the facility data"""
    if not date_str or not str(date_str).strip():
        return None
    
    date_str = str(date_str).strip()
    
    # Try various date formats
    formats = [
        '%m/%d/%Y',      # 8/2/2024
        '%d-%b-%y',      # 19-Oct-23
        '%d-%b-%Y',      # 19-Oct-2023
        '%d-%B-%y',      # 19-October-23
        '%d-%B-%Y',      # 19-October-2023
        '%m-%d-%Y',      # 08-02-2024
        '%Y-%m-%d',      # 2024-08-02
        '%d/%m/%Y',      # 2/8/2024
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try parsing with dateutil if available
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except ImportError:
        pass
    except ValueError:
        pass
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def extract_social_media_links(row: Dict[str, str]) -> Dict[str, str]:
    """Extract social media links from row data"""
    social_media = {}
    
    # Map column names to social media platforms
    social_mapping = {
        'website': 'website',
        'facebook': 'facebook',
        'instagram': 'instagram',
        'tiktok': 'tiktok',
        'youtube': 'youtube',
        'tripadvisor': 'tripadvisor',
        'yelp': 'yelp',
        'other': 'other',
        'zoochat': 'zoochat',
    }
    
    for col_key, platform in social_mapping.items():
        # Try both capitalized and lowercase
        for col_name in [col_key.capitalize(), col_key.upper(), col_key]:
            if col_name in row:
                url = row.get(col_name, '').strip()
                if url and url != 'None' and url != '':
                    if url.startswith('http') or url.startswith('www.'):
                        social_media[platform] = url
                    elif '@' in url:
                        # Handle Instagram/TikTok handles
                        social_media[platform] = url
    
    return social_media


def parse_facility_row(row: Dict[str, str], line_num: int) -> Optional[Dict[str, Any]]:
    """Parse a single facility row into facility data structure"""
    # Skip total row
    if row.get('Exhibitor', '').upper() == 'TOTAL':
        return None
    
    exhibitor = row.get('Exhibitor', '').strip()
    # Skip if exhibitor name is empty, URL, or just whitespace
    if not exhibitor or exhibitor.startswith('http') or exhibitor.startswith('www.'):
        return None
    
    # Parse tiger count
    tiger_count_str = row.get('Tigers', '').strip()
    try:
        tiger_count = int(tiger_count_str) if tiger_count_str else 0
    except (ValueError, TypeError):
        tiger_count = 0
    
    # Parse IR date (skip if it's a URL)
    ir_date_str = row.get('IR date', '').strip()
    ir_date = None
    if ir_date_str and not ir_date_str.startswith('http'):
        ir_date = parse_date(ir_date_str)
    
    # Extract social media links
    social_media = extract_social_media_links(row)
    
    # Get website from social_media if available, otherwise from Website column
    website = social_media.get('website') or row.get('Website', '').strip()
    if website:
        social_media.pop('website', None)  # Remove from social_media as it's stored separately
    
    facility_data = {
        'exhibitor_name': exhibitor,
        'usda_license': row.get('License', '').strip(),
        'state': row.get('State', '').strip(),
        'tiger_count': tiger_count,
        'ir_date': ir_date,
        'website': website if website and website != 'None' else None,
        'social_media_links': social_media,
        'accreditation_status': 'Non-Accredited',
        'is_reference_facility': True,
        'data_source': 'non_accredited_facilities',
        'reference_dataset_version': datetime.utcnow(),
        'reference_metadata': {
            'site': row.get('Site', '').strip(),
            'original_line': line_num,
            'import_timestamp': datetime.utcnow().isoformat(),
        }
    }
    
    return facility_data


def parse_facility_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse the tab-separated facility file"""
    facilities = []
    
    logger.info(f"Parsing facility file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read header
        header_line = f.readline().strip()
        headers = [h.strip() for h in header_line.split('\t')]
        
        logger.info(f"Found columns: {headers}")
        
        # Read data rows
        for line_num, line in enumerate(f, start=2):  # Start at 2 (after header)
            line = line.strip()
            if not line:
                continue
            
            # Parse tab-separated values
            values = [v.strip() for v in line.split('\t')]
            
            # Create row dictionary
            row = {headers[i]: values[i] if i < len(values) else '' for i in range(len(headers))}
            
            # Parse facility data
            facility_data = parse_facility_row(row, line_num)
            if facility_data:
                facilities.append(facility_data)
    
    logger.info(f"Parsed {len(facilities)} facilities from file")
    return facilities


def enrich_facilities(
    facilities_data: List[Dict[str, Any]],
    create_tigers: bool = False,
    dry_run: bool = False,
    db_session = None
) -> Dict[str, Any]:
    """Enrich database with facility data
    
    Args:
        facilities_data: List of facility data dictionaries
        create_tigers: Whether to create tiger records
        dry_run: If True, don't actually modify database
        db_session: Optional existing database session to use
    """
    stats = {
        'facilities_created': 0,
        'facilities_updated': 0,
        'facilities_skipped': 0,
        'tigers_created': 0,
        'errors': []
    }
    
    # Use provided session or create new one
    if db_session:
        db = db_session
        should_close = False
    else:
        db = get_sqlite_session().__enter__()
        should_close = True
    
    try:
        facility_service = FacilityService(db)
        
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
                    logger.info(f"Updating facility: {exhibitor_name}")
                    
                    if not dry_run:
                        # Update fields that are missing or should be updated
                        for key, value in facility_data.items():
                            if key == 'facility_id':
                                continue
                            
                            current_value = getattr(existing_facility, key, None)
                            
                            if key == 'social_media_links' and isinstance(value, dict):
                                # Merge social media links
                                current_links = current_value if isinstance(current_value, dict) else {}
                                current_links.update(value)
                                setattr(existing_facility, key, current_links)
                            elif current_value is None or current_value == [] or current_value == {}:
                                setattr(existing_facility, key, value)
                            elif key in ['is_reference_facility', 'data_source', 'reference_dataset_version']:
                                # Always update reference fields
                                setattr(existing_facility, key, value)
                    
                    stats['facilities_updated'] += 1
                    facility = existing_facility
                else:
                    # Create new facility
                    logger.info(f"Creating facility: {exhibitor_name}")
                    
                    if not dry_run:
                        # Create Facility object directly to include all fields
                        facility = Facility(
                            facility_id=uuid4(),
                            exhibitor_name=facility_data['exhibitor_name'],
                            usda_license=facility_data.get('usda_license'),
                            state=facility_data.get('state'),
                            tiger_count=facility_data.get('tiger_count', 0),
                            social_media_links=facility_data.get('social_media_links', {}),
                            website=facility_data.get('website'),
                            accreditation_status=facility_data.get('accreditation_status'),
                            ir_date=facility_data.get('ir_date'),
                            is_reference_facility=facility_data.get('is_reference_facility', False),
                            data_source=facility_data.get('data_source'),
                            reference_dataset_version=facility_data.get('reference_dataset_version'),
                            reference_metadata=facility_data.get('reference_metadata', {})
                        )
                        db.add(facility)
                        
                        db.commit()
                        db.refresh(facility)
                    else:
                        facility = None
                    
                    stats['facilities_created'] += 1
                
                # Create tigers if requested
                if create_tigers and not dry_run and facility:
                    tiger_count = facility_data.get('tiger_count', 0)
                    if tiger_count > 0:
                        # Count existing tigers for this facility
                        existing_tigers_count = db.query(Tiger).filter(
                            Tiger.origin_facility_id == facility.facility_id
                        ).count()
                        
                        # Create additional tigers if needed
                        for i in range(existing_tigers_count, tiger_count):
                            tiger = Tiger(
                                tiger_id=uuid4(),
                                name=f"{exhibitor_name} Tiger #{i+1}",
                                origin_facility_id=facility.facility_id,
                                last_seen_location=facility.state or "Unknown",
                                status=TigerStatus.active,
                                tags=["enriched", "non-accredited"],
                                notes=f"Enriched from facility data. Total tigers at facility: {tiger_count}"
                            )
                            db.add(tiger)
                            stats['tigers_created'] += 1
                        
                        if stats['tigers_created'] > 0 and not db_session:
                            db.commit()
                
            except Exception as e:
                error_msg = f"Error processing facility {facility_data.get('exhibitor_name', 'Unknown')}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                stats['errors'].append(error_msg)
                stats['facilities_skipped'] += 1
        
        # Only commit if we're managing the session
        if not dry_run and not db_session:
            db.commit()
    
    finally:
        if should_close:
            get_sqlite_session().__exit__(None, None, None)
    
    return stats


def enrich_from_datasets(create_tigers: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    """Enrich with data from ATRW and other datasets"""
    # This can be expanded to load tiger images from ATRW dataset
    # For now, we'll just log that this is available
    logger.info("Dataset enrichment (ATRW, etc.) can be done via ingest_datasets.py")
    return {}


def main():
    parser = argparse.ArgumentParser(
        description='Enrich SQLite demo database with facility data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python setup/scripts/enrich_facilities.py
  python setup/scripts/enrich_facilities.py --create-tigers
  python setup/scripts/enrich_facilities.py --dry-run
        """
    )
    parser.add_argument(
        '--facility-file',
        type=str,
        default='data/datasets/non-accredited-facilities',
        help='Path to facility data file (default: data/datasets/non-accredited-facilities)'
    )
    parser.add_argument(
        '--create-tigers',
        action='store_true',
        help='Create Tiger records based on tiger counts'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually modifying the database'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database before enrichment'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize database if requested
        if args.init_db:
            logger.info("Initializing SQLite database...")
            init_sqlite_db()
            logger.info("Database initialized")
        
        # Parse facility file
        facility_file = Path(args.facility_file)
        if not facility_file.exists():
            logger.error(f"Facility file not found: {facility_file}")
            sys.exit(1)
        
        facilities_data = parse_facility_file(facility_file)
        
        if args.dry_run:
            print(f"\n[DRY RUN] Would process {len(facilities_data)} facilities")
            print("\nSample facilities:")
            for i, fac in enumerate(facilities_data[:5]):
                print(f"  {i+1}. {fac['exhibitor_name']} ({fac.get('state', 'N/A')}) - {fac.get('tiger_count', 0)} tigers")
            if len(facilities_data) > 5:
                print(f"  ... and {len(facilities_data) - 5} more")
        else:
            # Enrich facilities
            print(f"\nEnriching database with {len(facilities_data)} facilities...")
            stats = enrich_facilities(
                facilities_data,
                create_tigers=args.create_tigers,
                dry_run=args.dry_run
            )
            
            print("\n" + "="*60)
            print("Enrichment Summary")
            print("="*60)
            print(f"Facilities created: {stats['facilities_created']}")
            print(f"Facilities updated: {stats['facilities_updated']}")
            print(f"Facilities skipped: {stats['facilities_skipped']}")
            if args.create_tigers:
                print(f"Tigers created: {stats['tigers_created']}")
            if stats['errors']:
                print(f"\nErrors: {len(stats['errors'])}")
                for error in stats['errors'][:10]:
                    print(f"  - {error}")
                if len(stats['errors']) > 10:
                    print(f"  ... and {len(stats['errors']) - 10} more errors")
            print("="*60)
            
            # Enrich from datasets if available
            dataset_stats = enrich_from_datasets(
                create_tigers=args.create_tigers,
                dry_run=args.dry_run
            )
        
        print("\n✓ Enrichment complete!")
        
    except Exception as e:
        logger.error(f"Enrichment failed: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()


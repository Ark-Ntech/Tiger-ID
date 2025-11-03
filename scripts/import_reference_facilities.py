"""Script to import reference facility dataset from Excel file

This script imports the TPC Tigers non-accredited facilities dataset
and marks them as reference facilities for prioritization and matching.

Usage:
    python scripts/import_reference_facilities.py "path/to/reference_data.xlsx"
    python scripts/import_reference_facilities.py "path/to/reference_data.xlsx" --create-verifications
"""

import argparse
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_db_session, Facility
from backend.services.facility_service import FacilityService
from backend.services.verification_service import VerificationService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def parse_reference_spreadsheet(file_path: str) -> pd.DataFrame:
    """Parse reference facility spreadsheet file"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    logger.info(f"Parsed spreadsheet with {len(df)} rows and {len(df.columns)} columns")
    logger.debug(f"Columns: {list(df.columns)}")
    
    return df


def normalize_column_name(col: str) -> str:
    """Normalize column name to lowercase with underscores"""
    return col.lower().strip().replace(' ', '_').replace('-', '_')


def extract_social_media_links(row: pd.Series) -> Dict[str, str]:
    """Extract social media links from row data"""
    social_media = {}
    
    # Common social media column patterns
    social_patterns = {
        'facebook': ['facebook', 'fb'],
        'instagram': ['instagram', 'ig'],
        'twitter': ['twitter', 'x'],
        'youtube': ['youtube', 'yt'],
        'website': ['website', 'url', 'site', 'web']
    }
    
    for platform, patterns in social_patterns.items():
        for pattern in patterns:
            # Check exact matches
            if pattern in row.index:
                url = row.get(pattern)
                if pd.notna(url) and str(url).strip():
                    social_media[platform] = str(url).strip()
                    break
            
            # Check fuzzy matches in column names
            for col in row.index:
                normalized_col = normalize_column_name(str(col))
                if pattern in normalized_col:
                    url = row.get(col)
                    if pd.notna(url) and str(url).strip():
                        # Extract URL if it's in a longer string
                        url_str = str(url).strip()
                        if 'http' in url_str:
                            social_media[platform] = url_str
                            break
    
    # Extract website separately if not already found
    if 'website' not in social_media:
        for col in ['website', 'url', 'site', 'web', 'homepage']:
            if col in row.index:
                url = row.get(col)
                if pd.notna(url) and str(url).strip() and 'http' in str(url):
                    social_media['website'] = str(url).strip()
                    break
    
    return social_media


def map_facility_data(row: pd.Series) -> Dict[str, Any]:
    """Map row data to facility fields"""
    # Normalize column names
    normalized_columns = {normalize_column_name(str(col)): col for col in row.index}
    
    facility_data = {}
    
    # Map exhibitor name
    for pattern in ['exhibitor_name', 'exhibitor', 'name', 'facility_name', 'facility']:
        if pattern in normalized_columns:
            value = row.get(normalized_columns[pattern])
            if pd.notna(value):
                facility_data['exhibitor_name'] = str(value).strip()
                break
    
    # Map USDA license
    for pattern in ['usda_license', 'usda', 'license', 'license_number', 'licence']:
        if pattern in normalized_columns:
            value = row.get(normalized_columns[pattern])
            if pd.notna(value):
                facility_data['usda_license'] = str(value).strip()
                break
    
    # Map state
    for pattern in ['state', 'location_state', 'st']:
        if pattern in normalized_columns:
            value = row.get(normalized_columns[pattern])
            if pd.notna(value):
                facility_data['state'] = str(value).strip()
                break
    
    # Map city
    for pattern in ['city', 'location_city']:
        if pattern in normalized_columns:
            value = row.get(normalized_columns[pattern])
            if pd.notna(value):
                facility_data['city'] = str(value).strip()
                break
    
    # Map address
    for pattern in ['address', 'location_address', 'street_address']:
        if pattern in normalized_columns:
            value = row.get(normalized_columns[pattern])
            if pd.notna(value):
                facility_data['address'] = str(value).strip()
                break
    
    # Map tiger count
    for pattern in ['tiger_count', 'tigers', 'num_tigers', 'tiger_number']:
        if pattern in normalized_columns:
            value = row.get(normalized_columns[pattern])
            if pd.notna(value) and str(value).strip():
                try:
                    facility_data['tiger_count'] = int(float(value))
                except (ValueError, TypeError):
                    pass
                break
    
    # Extract social media links
    social_media = extract_social_media_links(row)
    if social_media:
        facility_data['social_media_links'] = social_media
        # Extract website if separate
        if 'website' in social_media:
            facility_data['website'] = social_media['website']
    
    # Map accreditation status
    for pattern in ['accreditation', 'accreditation_status', 'status']:
        if pattern in normalized_columns:
            value = row.get(normalized_columns[pattern])
            if pd.notna(value):
                facility_data['accreditation_status'] = str(value).strip()
                break
    
    return facility_data


def import_reference_facilities(
    df: pd.DataFrame,
    session,
    create_verifications: bool = False
) -> Dict[str, Any]:
    """Import reference facilities from DataFrame"""
    facility_service = FacilityService(session)
    verification_service = VerificationService(session) if create_verifications else None
    
    imported_count = 0
    updated_count = 0
    created_count = 0
    skipped_count = 0
    errors = []
    
    import_timestamp = datetime.utcnow()
    
    for idx, row in df.iterrows():
        try:
            # Map row data to facility structure
            facility_data = map_facility_data(row)
            
            # Skip if no exhibitor name or USDA license
            if not facility_data.get('exhibitor_name') and not facility_data.get('usda_license'):
                logger.warning(f"Row {idx}: Skipping - no exhibitor name or USDA license")
                skipped_count += 1
                continue
            
            # Set reference data fields
            facility_data['is_reference_facility'] = True
            facility_data['data_source'] = 'tpc_reference'
            facility_data['reference_dataset_version'] = import_timestamp
            
            # Store original row data in reference_metadata
            reference_metadata = {
                'original_row_index': int(idx),
                'original_columns': {str(col): str(row.get(col)) if pd.notna(row.get(col)) else None 
                                   for col in row.index},
                'import_timestamp': import_timestamp.isoformat(),
                'import_file': str(Path(__file__).name)
            }
            facility_data['reference_metadata'] = reference_metadata
            
            # Check if facility already exists
            existing_facility = None
            
            # First try by USDA license
            if facility_data.get('usda_license'):
                existing_facility = facility_service.get_facility_by_license(facility_data['usda_license'])
            
            # If not found, try by name (fuzzy match)
            if not existing_facility and facility_data.get('exhibitor_name'):
                facilities = facility_service.get_facilities(
                    search_query=facility_data['exhibitor_name'],
                    limit=10
                )
                # Exact name match
                for fac in facilities:
                    if fac.exhibitor_name.lower() == facility_data['exhibitor_name'].lower():
                        existing_facility = fac
                        break
            
            if existing_facility:
                # Update existing facility
                logger.info(f"Updating existing facility: {existing_facility.exhibitor_name} (ID: {existing_facility.facility_id})")
                
                # Update fields
                for key, value in facility_data.items():
                    if key in ['is_reference_facility', 'data_source', 'reference_dataset_version', 'reference_metadata']:
                        # Always update reference data fields
                        setattr(existing_facility, key, value)
                    elif key != 'facility_id' and hasattr(existing_facility, key):
                        # Only update if current value is None/empty or if it's social_media_links
                        current_value = getattr(existing_facility, key)
                        if current_value is None or current_value == [] or current_value == {}:
                            setattr(existing_facility, key, value)
                        elif key == 'social_media_links' and isinstance(value, dict):
                            # Merge social media links
                            current_links = current_value if isinstance(current_value, dict) else {}
                            current_links.update(value)
                            setattr(existing_facility, key, current_links)
                
                session.commit()
                session.refresh(existing_facility)
                
                updated_count += 1
                
                if create_verifications and verification_service:
                    verification_service.create_verification_request(
                        entity_type='facility',
                        entity_id=existing_facility.facility_id,
                        priority='high'  # Reference facilities get high priority
                    )
                
                imported_count += 1
            else:
                # Create new facility
                logger.info(f"Creating new facility: {facility_data.get('exhibitor_name', 'Unknown')}")
                
                facility = facility_service.create_facility(
                    exhibitor_name=facility_data.get('exhibitor_name', 'Unknown'),
                    usda_license=facility_data.get('usda_license'),
                    state=facility_data.get('state'),
                    city=facility_data.get('city'),
                    address=facility_data.get('address'),
                    tiger_count=facility_data.get('tiger_count', 0),
                    social_media_links=facility_data.get('social_media_links', {}),
                    website=facility_data.get('website'),
                    accreditation_status=facility_data.get('accreditation_status')
                )
                
                # Set reference data fields
                facility.is_reference_facility = True
                facility.data_source = 'tpc_reference'
                facility.reference_dataset_version = import_timestamp
                facility.reference_metadata = reference_metadata
                
                session.commit()
                session.refresh(facility)
                
                created_count += 1
                imported_count += 1
                
                if create_verifications and verification_service:
                    verification_service.create_verification_request(
                        entity_type='facility',
                        entity_id=facility.facility_id,
                        priority='high'  # Reference facilities get high priority
                    )
        
        except Exception as e:
            error_msg = f"Row {idx}: Error importing facility - {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            skipped_count += 1
    
    session.commit()
    
    return {
        'imported_count': imported_count,
        'created_count': created_count,
        'updated_count': updated_count,
        'skipped_count': skipped_count,
        'errors': errors,
        'total_rows': len(df)
    }


def main():
    parser = argparse.ArgumentParser(
        description='Import reference facility dataset from Excel file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python scripts/import_reference_facilities.py "data/reference_facilities.xlsx"
  python scripts/import_reference_facilities.py "data/reference_facilities.xlsx" --create-verifications
        """
    )
    parser.add_argument(
        'file',
        type=str,
        help='Path to reference facility Excel file (.xlsx or .xls)'
    )
    parser.add_argument(
        '--create-verifications',
        action='store_true',
        help='Create verification requests for imported facilities'
    )
    
    args = parser.parse_args()
    
    try:
        # Parse spreadsheet
        print(f"Parsing reference facility spreadsheet: {args.file}")
        df = parse_reference_spreadsheet(args.file)
        print(f"Loaded {len(df)} rows")
        print(f"Columns: {', '.join(df.columns[:10])}" + ('...' if len(df.columns) > 10 else ''))
        
        # Import facilities
        with get_db_session() as session:
            print("\nImporting facilities...")
            results = import_reference_facilities(
                df,
                session,
                create_verifications=args.create_verifications
            )
            
            print(f"\nImport Summary:")
            print(f"  Total rows processed: {results['total_rows']}")
            print(f"  Successfully imported: {results['imported_count']}")
            print(f"    - Created new: {results['created_count']}")
            print(f"    - Updated existing: {results['updated_count']}")
            print(f"  Skipped: {results['skipped_count']}")
            
            if results['errors']:
                print(f"\nErrors encountered: {len(results['errors'])}")
                for error in results['errors'][:10]:  # Show first 10 errors
                    print(f"  - {error}")
                if len(results['errors']) > 10:
                    print(f"  ... and {len(results['errors']) - 10} more errors")
            
            if args.create_verifications:
                print(f"\nVerification requests created for imported facilities")
        
        print("\nImport complete!")
        
    except Exception as e:
        logger.error(f"Import failed: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()


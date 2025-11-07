#!/usr/bin/env python3
"""
Parse TPC_Tigers non-accredited facilities Excel file.

This script extracts facility data from the Excel file and prepares it
for database insertion.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.logging import get_logger

logger = get_logger(__name__)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various date formats from the facility data"""
    if not date_str or pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ['none', 'nan', '']:
        return None
    
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
        '%Y/%m/%d',      # 2024/08/02
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
    except (ValueError, TypeError):
        pass
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def extract_social_media_links(row: pd.Series) -> Dict[str, str]:
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
        # Try various column name variations
        for col_name in [col_key, col_key.capitalize(), col_key.upper(), 
                         col_key.title(), f'{col_key}_url', f'{col_key}_link']:
            if col_name in row.index:
                url = row.get(col_name, '')
                if pd.notna(url):
                    url = str(url).strip()
                    if url and url.lower() not in ['none', 'nan', '']:
                        if url.startswith('http') or url.startswith('www.'):
                            social_media[platform] = url
                        elif '@' in url:
                            # Handle Instagram/TikTok handles
                            social_media[platform] = url
    
    return social_media


def parse_facility_row(row: pd.Series, row_num: int) -> Optional[Dict[str, Any]]:
    """Parse a single facility row into facility data structure"""
    # Skip total row
    exhibitor = str(row.get('Exhibitor', '')).strip()
    if not exhibitor or exhibitor.upper() == 'TOTAL' or exhibitor.startswith('http'):
        return None
    
    # Parse tiger count
    tiger_count_str = row.get('Tigers', '')
    try:
        tiger_count = int(float(tiger_count_str)) if pd.notna(tiger_count_str) else 0
    except (ValueError, TypeError):
        tiger_count = 0
    
    # Parse IR date
    ir_date_str = row.get('IR date', '')
    ir_date = None
    if pd.notna(ir_date_str):
        ir_date_str = str(ir_date_str).strip()
        if ir_date_str and not ir_date_str.startswith('http'):
            ir_date = parse_date(ir_date_str)
    
    # Extract social media links
    social_media = extract_social_media_links(row)
    
    # Get website from social_media if available, otherwise from Website column
    website = social_media.get('website') or row.get('Website', '')
    if pd.notna(website):
        website = str(website).strip()
        if website and website.lower() not in ['none', 'nan', '']:
            if not website.startswith('http') and not website.startswith('www.'):
                website = None
        else:
            website = None
    else:
        website = None
    
    if website:
        social_media.pop('website', None)  # Remove from social_media as it's stored separately
    
    # Get state
    state = row.get('State', '')
    if pd.notna(state):
        state = str(state).strip()
    else:
        state = None
    
    # Get city
    city = row.get('City', '')
    if pd.notna(city):
        city = str(city).strip()
    else:
        city = None
    
    # Get address
    address = row.get('Address', '')
    if pd.notna(address):
        address = str(address).strip()
    else:
        address = None
    
    # Get USDA license
    usda_license = row.get('License', '')
    if pd.notna(usda_license):
        usda_license = str(usda_license).strip()
    else:
        usda_license = None
    
    # Get site
    site = row.get('Site', '')
    if pd.notna(site):
        site = str(site).strip()
    else:
        site = None
    
    facility_data = {
        'exhibitor_name': exhibitor,
        'usda_license': usda_license,
        'state': state,
        'city': city,
        'address': address,
        'tiger_count': tiger_count,
        'ir_date': ir_date,
        'website': website,
        'social_media_links': social_media,
        'accreditation_status': 'Non-Accredited',
        'is_reference_facility': True,
        'data_source': 'tpc_non_accredited_facilities',
        'reference_dataset_version': datetime.utcnow(),
        'reference_metadata': {
            'site': site,
            'original_row': row_num,
            'import_timestamp': datetime.utcnow().isoformat(),
        }
    }
    
    return facility_data


def parse_excel_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse the Excel facility file"""
    facilities = []
    
    logger.info(f"Parsing Excel file: {file_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        
        logger.info(f"Loaded {len(df)} rows from Excel file")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Process each row
        for idx, row in df.iterrows():
            facility_data = parse_facility_row(row, idx + 2)  # +2 because Excel rows start at 1 and header is row 1
            if facility_data:
                facilities.append(facility_data)
        
        logger.info(f"Parsed {len(facilities)} facilities from Excel file")
        
    except Exception as e:
        logger.error(f"Error parsing Excel file: {e}", exc_info=True)
        raise
    
    return facilities


def main():
    parser = argparse.ArgumentParser(description='Parse TPC_Tigers Excel file')
    parser.add_argument('file', type=str, help='Path to Excel file')
    parser.add_argument('--output', type=str, help='Output JSON file path (optional)')
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return 1
    
    # Parse Excel file
    facilities = parse_excel_file(file_path)
    
    print(f"\n✓ Parsed {len(facilities)} facilities from Excel file")
    
    # Optionally save to JSON
    if args.output:
        import json
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(facilities, f, indent=2, default=str)
        print(f"✓ Saved to {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


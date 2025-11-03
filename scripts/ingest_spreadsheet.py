"""Script to ingest spreadsheet data into the database"""

import argparse
import pandas as pd
import sys
from pathlib import Path
from uuid import uuid4
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from uuid import UUID
from backend.database import get_db_session, Facility, Tiger, Investigation
from backend.services.facility_service import FacilityService
from backend.services.tiger_service import TigerService
from backend.services.investigation_service import InvestigationService
from backend.services.verification_service import VerificationService


def parse_spreadsheet(file_path: str) -> pd.DataFrame:
    """Parse spreadsheet file"""
    file_path = Path(file_path)
    
    if file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    return df


def ingest_facilities(df: pd.DataFrame, session) -> List[Facility]:
    """Ingest facility data from spreadsheet"""
    facility_service = FacilityService(session)
    facilities = []
    
    # Map common column names
    column_mapping = {
        'exhibitor_name': ['exhibitor_name', 'exhibitor', 'name', 'facility_name'],
        'usda_license': ['usda_license', 'usda', 'license', 'license_number'],
        'state': ['state', 'location_state'],
        'city': ['city', 'location_city'],
        'address': ['address', 'location_address'],
        'tiger_count': ['tiger_count', 'tigers', 'num_tigers']
    }
    
    for _, row in df.iterrows():
        facility_data = {}
        
        # Map columns
        for target_col, possible_cols in column_mapping.items():
            for col in possible_cols:
                if col in row and pd.notna(row[col]):
                    facility_data[target_col] = row[col]
                    break
        
        # Create or update facility
        if 'usda_license' in facility_data:
            facility = session.query(Facility).filter(
                Facility.usda_license == facility_data['usda_license']
            ).first()
            
            if facility:
                # Update existing
                for key, value in facility_data.items():
                    if hasattr(facility, key):
                        setattr(facility, key, value)
            else:
                # Create new
                facility = Facility(
                    exhibitor_name=facility_data.get('exhibitor_name', 'Unknown'),
                    usda_license=facility_data['usda_license'],
                    state=facility_data.get('state'),
                    city=facility_data.get('city'),
                    address=facility_data.get('address'),
                    tiger_count=int(facility_data.get('tiger_count', 0)) if pd.notna(facility_data.get('tiger_count')) else 0
                )
                session.add(facility)
            
            facilities.append(facility)
    
    session.commit()
    return facilities


def ingest_tigers(df: pd.DataFrame, session, investigation_id: str = None) -> List[Tiger]:
    """Ingest tiger data from spreadsheet"""
    tiger_service = TigerService(session)
    tigers = []
    
    # Map common column names
    column_mapping = {
        'name': ['name', 'tiger_name', 'individual_name'],
        'alias': ['alias', 'aliases', 'other_names'],
        'status': ['status', 'tiger_status'],
        'last_seen_location': ['last_seen_location', 'location', 'last_location'],
        'origin_facility_id': ['origin_facility_id', 'facility_id']
    }
    
    for _, row in df.iterrows():
        tiger_data = {}
        
        # Map columns
        for target_col, possible_cols in column_mapping.items():
            for col in possible_cols:
                if col in row and pd.notna(row[col]):
                    tiger_data[target_col] = row[col]
                    break
        
        # Create tiger
        if 'name' in tiger_data or 'alias' in tiger_data:
            tiger = Tiger(
                name=tiger_data.get('name'),
                alias=tiger_data.get('alias'),
                status=tiger_data.get('status', 'unknown'),
                last_seen_location=tiger_data.get('last_seen_location'),
                origin_facility_id=UUID(tiger_data['origin_facility_id']) if tiger_data.get('origin_facility_id') else None
            )
            session.add(tiger)
            tigers.append(tiger)
    
    session.commit()
    return tigers


def create_verification_requests(entities: List[Any], entity_type: str, session):
    """Create verification requests for ingested entities"""
    verification_service = VerificationService(session)
    
    for entity in entities:
        verification_service.create_verification_request(
            entity_type=entity_type,
            entity_id=entity.tiger_id if entity_type == 'tiger' else entity.facility_id,
            priority='medium'
        )
    
    session.commit()


def main():
    parser = argparse.ArgumentParser(description='Ingest spreadsheet data into database')
    parser.add_argument('file', type=str, help='Path to spreadsheet file')
    parser.add_argument('--type', type=str, choices=['facilities', 'tigers', 'auto'], 
                       default='auto', help='Type of data to ingest')
    parser.add_argument('--create-investigation', action='store_true',
                       help='Create investigation for ingested data')
    parser.add_argument('--create-verifications', action='store_true',
                       help='Create verification requests for ingested entities')
    
    args = parser.parse_args()
    
    # Parse spreadsheet
    print(f"Parsing spreadsheet: {args.file}")
    df = parse_spreadsheet(args.file)
    print(f"Loaded {len(df)} rows")
    
    # Auto-detect type if needed
    if args.type == 'auto':
        if 'usda_license' in df.columns or 'facility' in str(df.columns).lower():
            args.type = 'facilities'
        elif 'tiger' in str(df.columns).lower() or 'name' in df.columns:
            args.type = 'tigers'
        else:
            print("Could not auto-detect data type. Please specify --type")
            return
    
    # Ingest data
    with get_db_session() as session:
        investigation_id = None
        
        if args.create_investigation:
            investigation_service = InvestigationService(session)
            investigation = investigation_service.create_investigation(
                title=f"Bulk Import: {Path(args.file).name}",
                created_by=uuid4(),  # TODO: Use actual user ID
                description=f"Bulk import from {args.file}",
                priority='medium'
            )
            investigation_id = str(investigation.investigation_id)
            print(f"Created investigation: {investigation_id}")
        
        if args.type == 'facilities':
            print("Ingesting facilities...")
            facilities = ingest_facilities(df, session)
            print(f"Ingested {len(facilities)} facilities")
            
            if args.create_verifications:
                create_verification_requests(facilities, 'facility', session)
                print("Created verification requests")
        
        elif args.type == 'tigers':
            print("Ingesting tigers...")
            tigers = ingest_tigers(df, session, investigation_id)
            print(f"Ingested {len(tigers)} tigers")
            
            if args.create_verifications:
                create_verification_requests(tigers, 'tiger', session)
                print("Created verification requests")
        
        print("Ingestion complete!")


if __name__ == "__main__":
    main()


"""Service layer for integrating external API data into database"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from backend.database.models import Facility, Evidence, BackgroundJob
from backend.services.external_apis.usda_client import USDAClient
from backend.services.external_apis.cites_client import CITESClient
from backend.services.external_apis.usfws_client import USFWSClient
from backend.services.external_apis.data_models import (
    USDAFacility,
    USDAInspectionReport,
    CITESTradeRecord,
    USFWSPermit
)
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class IntegrationService:
    """Service for integrating external API data into the database"""
    
    def __init__(
        self,
        session: Session,
        usda_client: Optional[USDAClient] = None,
        cites_client: Optional[CITESClient] = None,
        usfws_client: Optional[USFWSClient] = None
    ):
        """
        Initialize integration service
        
        Args:
            session: Database session
            usda_client: USDA API client
            cites_client: CITES API client
            usfws_client: USFWS API client
        """
        self.session = session
        self.usda_client = usda_client
        self.cites_client = cites_client
        self.usfws_client = usfws_client
    
    async def sync_facility_from_usda(
        self,
        license_number: str,
        investigation_id: Optional[UUID] = None
    ) -> Optional[Facility]:
        """
        Sync facility data from USDA API
        
        Args:
            license_number: USDA license number
            investigation_id: Optional investigation ID for evidence linking
        
        Returns:
            Facility record or None
        """
        if not self.usda_client:
            logger.warning("USDA client not available")
            return None
        
        try:
            # Get facility details from USDA
            facility_data = await self.usda_client.get_facility_details(license_number)
            if not facility_data:
                logger.warning("No facility data from USDA", license_number=license_number)
                return None
            
            # Find or create facility
            facility = self.session.query(Facility).filter(
                Facility.usda_license == license_number
            ).first()
            
            if not facility:
                facility = Facility(
                    exhibitor_name=facility_data.get("exhibitor_name", "Unknown"),
                    usda_license=license_number,
                    state=facility_data.get("state"),
                    city=facility_data.get("city"),
                    address=facility_data.get("address"),
                    tiger_count=facility_data.get("tiger_count", 0),
                    metadata={"usda_data": facility_data}
                )
                self.session.add(facility)
            else:
                # Update existing facility
                facility.exhibitor_name = facility_data.get("exhibitor_name", facility.exhibitor_name)
                facility.state = facility_data.get("state") or facility.state
                facility.city = facility_data.get("city") or facility.city
                facility.address = facility_data.get("address") or facility.address
                facility.tiger_count = facility_data.get("tiger_count", facility.tiger_count)
                if not facility.metadata:
                    facility.metadata = {}
                facility.metadata["usda_data"] = facility_data
                facility.updated_at = datetime.utcnow()
            
            # Get inspection reports
            inspections = await self.usda_client.get_inspection_reports(license_number)
            if inspections:
                violation_history = []
                last_inspection_date = None
                
                for inspection in inspections:
                    violations = inspection.get("violations", [])
                    violation_history.extend(violations)
                    
                    inspection_date = inspection.get("inspection_date")
                    if inspection_date and (not last_inspection_date or inspection_date > last_inspection_date):
                        last_inspection_date = inspection_date
                
                facility.violation_history = violation_history
                if last_inspection_date:
                    facility.last_inspection_date = last_inspection_date
                
                # Create evidence items for inspection reports
                if investigation_id:
                    for inspection in inspections:
                        evidence = Evidence(
                            investigation_id=investigation_id,
                            source_type="document",
                            source_url=f"https://www.aphis.usda.gov/inspection/{inspection.get('report_id')}",
                            content={
                                "inspection_report": inspection,
                                "facility_id": str(facility.facility_id)
                            },
                            extracted_text=f"Inspection Report: {inspection.get('findings', '')}",
                            metadata={"source": "usda", "report_id": inspection.get("report_id")}
                        )
                        self.session.add(evidence)
            
            self.session.commit()
            self.session.refresh(facility)
            
            logger.info("Synced facility from USDA", facility_id=str(facility.facility_id))
            return facility
            
        except Exception as e:
            logger.error("Failed to sync facility from USDA", error=str(e))
            self.session.rollback()
            return None
    
    async def sync_facility_inspections(
        self,
        facility_id: UUID,
        investigation_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Sync inspection reports for a facility
        
        Args:
            facility_id: Facility ID
            investigation_id: Optional investigation ID for evidence linking
        
        Returns:
            List of synced inspection reports
        """
        facility = self.session.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        
        if not facility or not facility.usda_license:
            logger.warning("Facility not found or missing USDA license", facility_id=str(facility_id))
            return []
        
        if not self.usda_client:
            logger.warning("USDA client not available")
            return []
        
        try:
            inspections = await self.usda_client.get_inspection_reports(facility.usda_license)
            synced = []
            
            for inspection in inspections:
                # Create evidence item for inspection
                if investigation_id:
                    evidence = Evidence(
                        investigation_id=investigation_id,
                        source_type="document",
                        source_url=f"https://www.aphis.usda.gov/inspection/{inspection.get('report_id')}",
                        content={"inspection_report": inspection},
                        extracted_text=f"Inspection Report: {inspection.get('findings', '')}",
                        metadata={"source": "usda", "report_id": inspection.get("report_id")}
                    )
                    self.session.add(evidence)
                
                synced.append(inspection)
            
            self.session.commit()
            logger.info("Synced inspections", facility_id=str(facility_id), count=len(synced))
            return synced
            
        except Exception as e:
            logger.error("Failed to sync inspections", error=str(e))
            self.session.rollback()
            return []
    
    async def sync_cites_trade_records(
        self,
        investigation_id: UUID,
        country_origin: Optional[str] = None,
        country_destination: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Sync CITES trade records for an investigation
        
        Args:
            investigation_id: Investigation ID
            country_origin: Origin country code
            country_destination: Destination country code
            year: Year to filter
            limit: Maximum records
        
        Returns:
            List of synced trade records
        """
        if not self.cites_client:
            logger.warning("CITES client not available")
            return []
        
        try:
            trade_records = await self.cites_client.get_tiger_trade_records(
                country_origin=country_origin,
                country_destination=country_destination,
                year=year,
                limit=limit
            )
            
            synced = []
            for record in trade_records:
                # Create evidence item for trade record
                evidence = Evidence(
                    investigation_id=investigation_id,
                    source_type="document",
                    source_url=f"https://trade.cites.org/record/{record.get('record_id')}",
                    content={"trade_record": record},
                    extracted_text=f"CITES Trade Record: {record.get('species')} from {record.get('country_origin')} to {record.get('country_destination')}",
                    metadata={"source": "cites", "record_id": record.get("record_id")}
                )
                self.session.add(evidence)
                synced.append(record)
            
            self.session.commit()
            logger.info("Synced CITES trade records", investigation_id=str(investigation_id), count=len(synced))
            return synced
            
        except Exception as e:
            logger.error("Failed to sync CITES trade records", error=str(e))
            self.session.rollback()
            return []
    
    async def sync_usfws_permits(
        self,
        investigation_id: UUID,
        permit_number: Optional[str] = None,
        applicant_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Sync USFWS permit records for an investigation
        
        Args:
            investigation_id: Investigation ID
            permit_number: Permit number to filter
            applicant_name: Applicant name to filter
            limit: Maximum records
        
        Returns:
            List of synced permit records
        """
        if not self.usfws_client:
            logger.warning("USFWS client not available")
            return []
        
        try:
            permits = await self.usfws_client.get_tiger_permit_records(
                applicant_name=applicant_name,
                limit=limit
            )
            
            if permit_number:
                permits = [p for p in permits if p.get("permit_number") == permit_number]
            
            synced = []
            for permit in permits:
                # Create evidence item for permit
                evidence = Evidence(
                    investigation_id=investigation_id,
                    source_type="document",
                    source_url=f"https://api.fws.gov/permits/{permit.get('permit_number')}",
                    content={"permit": permit},
                    extracted_text=f"USFWS Permit: {permit.get('permit_number')} for {permit.get('applicant_name')}",
                    metadata={"source": "usfws", "permit_number": permit.get("permit_number")}
                )
                self.session.add(evidence)
                synced.append(permit)
            
            self.session.commit()
            logger.info("Synced USFWS permits", investigation_id=str(investigation_id), count=len(synced))
            return synced
            
        except Exception as e:
            logger.error("Failed to sync USFWS permits", error=str(e))
            self.session.rollback()
            return []


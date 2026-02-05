"""API endpoints for dataset integration"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from backend.database import get_db
from backend.database.models import Facility, Investigation, BackgroundJob
from backend.services.integration_service import IntegrationService
from backend.services.external_apis.factory import get_api_clients
from backend.services.external_apis.atrw_dataset import ATRWDatasetManager
from sqlalchemy.orm import Session


# Note: Background task processing via Celery has been removed.
# All sync operations now run synchronously.

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


class SyncFacilityRequest(BaseModel):
    """Request model for facility sync"""
    license_number: str = Field(..., description="USDA license number")
    investigation_id: Optional[UUID] = Field(None, description="Optional investigation ID")


class SyncInspectionsRequest(BaseModel):
    """Request model for inspection sync"""
    facility_id: UUID = Field(..., description="Facility ID")
    investigation_id: Optional[UUID] = Field(None, description="Optional investigation ID")


class SyncCITESRequest(BaseModel):
    """Request model for CITES sync"""
    investigation_id: UUID = Field(..., description="Investigation ID")
    country_origin: Optional[str] = Field(None, description="Origin country code")
    country_destination: Optional[str] = Field(None, description="Destination country code")
    year: Optional[int] = Field(None, description="Year to filter")
    limit: int = Field(100, description="Maximum records")


class SyncUSFWSRequest(BaseModel):
    """Request model for USFWS sync"""
    investigation_id: UUID = Field(..., description="Investigation ID")
    permit_number: Optional[str] = Field(None, description="Permit number to filter")
    applicant_name: Optional[str] = Field(None, description="Applicant name to filter")
    limit: int = Field(100, description="Maximum records")


class DownloadATRWRequest(BaseModel):
    """Request model for ATRW dataset download"""
    dataset_dir: str = Field(..., description="Directory to store dataset")
    force: bool = Field(False, description="Force download even if exists")


@router.get("/health")
async def health_check():
    """Check integration API health"""
    clients = get_api_clients()
    
    health_status = {}
    for name, client in clients.items():
        if client:
            health_status[name] = await client.test_connection()
        else:
            health_status[name] = {"status": "disabled"}
    
    return {
        "status": "ok",
        "integrations": health_status
    }


@router.post("/usda/sync-facility")
async def sync_facility_usda(
    request: SyncFacilityRequest,
    db: Session = Depends(get_db),
    background: bool = False
):
    """
    Sync facility data from USDA API
    
    Args:
        request: Sync request with license number
        db: Database session
        background: Whether to run in background
    
    Returns:
        Sync result with facility data
    """
    clients = get_api_clients()
    if not clients["usda"]:
        raise HTTPException(status_code=503, detail="USDA integration not enabled")
    
    if background:
        raise HTTPException(
            status_code=501,
            detail="Background processing not available. Set background=false to run synchronously."
        )

    # Run synchronously
    integration_service = IntegrationService(
        session=db,
        usda_client=clients["usda"],
        cites_client=clients["cites"],
        usfws_client=clients["usfws"]
    )
    
    facility = await integration_service.sync_facility_from_usda(
        license_number=request.license_number,
        investigation_id=request.investigation_id
    )
    
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found in USDA database")
    
    return {
        "status": "success",
        "facility_id": str(facility.facility_id),
        "facility": {
            "exhibitor_name": facility.exhibitor_name,
            "usda_license": facility.usda_license,
            "state": facility.state,
            "city": facility.city
        }
    }


@router.post("/usda/sync-inspections")
async def sync_inspections(
    request: SyncInspectionsRequest,
    db: Session = Depends(get_db),
    background: bool = False
):
    """
    Sync inspection reports for a facility
    
    Args:
        request: Sync request with facility ID
        db: Database session
        background: Whether to run in background
    
    Returns:
        Sync result with inspection reports
    """
    clients = get_api_clients()
    if not clients["usda"]:
        raise HTTPException(status_code=503, detail="USDA integration not enabled")
    
    if background:
        raise HTTPException(
            status_code=501,
            detail="Background processing not available. Set background=false to run synchronously."
        )

    integration_service = IntegrationService(
        session=db,
        usda_client=clients["usda"],
        cites_client=clients["cites"],
        usfws_client=clients["usfws"]
    )
    
    inspections = await integration_service.sync_facility_inspections(
        facility_id=request.facility_id,
        investigation_id=request.investigation_id
    )
    
    return {
        "status": "success",
        "count": len(inspections),
        "inspections": inspections
    }


@router.post("/cites/sync-trade-records")
async def sync_cites_trade_records(
    request: SyncCITESRequest,
    db: Session = Depends(get_db),
    background: bool = False
):
    """
    Sync CITES trade records for an investigation
    
    Args:
        request: Sync request with investigation ID
        db: Database session
        background: Whether to run in background
    
    Returns:
        Sync result with trade records
    """
    clients = get_api_clients()
    if not clients["cites"]:
        raise HTTPException(status_code=503, detail="CITES integration not enabled")
    
    if background:
        raise HTTPException(
            status_code=501,
            detail="Background processing not available. Set background=false to run synchronously."
        )

    integration_service = IntegrationService(
        session=db,
        usda_client=clients["usda"],
        cites_client=clients["cites"],
        usfws_client=clients["usfws"]
    )
    
    records = await integration_service.sync_cites_trade_records(
        investigation_id=request.investigation_id,
        country_origin=request.country_origin,
        country_destination=request.country_destination,
        year=request.year,
        limit=request.limit
    )
    
    return {
        "status": "success",
        "count": len(records),
        "records": records
    }


@router.post("/usfws/sync-permits")
async def sync_usfws_permits(
    request: SyncUSFWSRequest,
    db: Session = Depends(get_db),
    background: bool = False
):
    """
    Sync USFWS permit records for an investigation
    
    Args:
        request: Sync request with investigation ID
        db: Database session
        background: Whether to run in background
    
    Returns:
        Sync result with permit records
    """
    clients = get_api_clients()
    if not clients["usfws"]:
        raise HTTPException(status_code=503, detail="USFWS integration not enabled")
    
    if background:
        raise HTTPException(
            status_code=501,
            detail="Background processing not available. Set background=false to run synchronously."
        )

    integration_service = IntegrationService(
        session=db,
        usda_client=clients["usda"],
        cites_client=clients["cites"],
        usfws_client=clients["usfws"]
    )
    
    permits = await integration_service.sync_usfws_permits(
        investigation_id=request.investigation_id,
        permit_number=request.permit_number,
        applicant_name=request.applicant_name,
        limit=request.limit
    )
    
    return {
        "status": "success",
        "count": len(permits),
        "permits": permits
    }


@router.post("/atrw/download")
async def download_atrw_dataset(
    request: DownloadATRWRequest,
    background: bool = True
):
    """
    Download ATRW dataset
    
    Args:
        request: Download request with dataset directory
        background: Whether to run in background (default: True)
    
    Returns:
        Download status
    """
    if background:
        raise HTTPException(
            status_code=501,
            detail="Background processing not available. Set background=false to run synchronously."
        )

    import asyncio
    manager = ATRWDatasetManager(dataset_dir=request.dataset_dir)
    result = await manager.download_dataset(force=request.force)
    return result


@router.get("/atrw/info")
async def get_atrw_info(dataset_dir: str = "./data/models/atrw"):
    """
    Get ATRW dataset information
    
    Args:
        dataset_dir: Dataset directory path
    
    Returns:
        Dataset information
    """
    import asyncio
    manager = ATRWDatasetManager(dataset_dir=dataset_dir)
    info = manager.get_dataset_info()
    metadata = await manager.get_dataset_metadata()
    
    return {
        "info": info,
        "metadata": metadata,
        "exists": await manager.check_dataset_exists()
    }


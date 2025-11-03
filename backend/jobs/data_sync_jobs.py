"""Celery background jobs for data synchronization"""

from celery import Celery
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from backend.database import SessionLocal, get_db_session
from backend.database.models import Facility, BackgroundJob
from backend.utils.db_helpers import with_db_session
from backend.services.external_apis.factory import get_api_clients
from backend.services.integration_service import IntegrationService
from backend.services.external_apis.atrw_dataset import ATRWDatasetManager
from backend.utils.logging import get_logger
from backend.utils.uuid_helpers import safe_uuid, parse_uuid

logger = get_logger(__name__)

# Import news monitoring job
try:
    from backend.jobs.news_monitoring_job import monitor_news_articles
except ImportError:
    monitor_news_articles = None

# Initialize Celery app (configuration should come from settings)
celery_app = Celery("tiger_investigation")

# Configure Celery Beat schedule for periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Periodic facility sync - daily at 2 AM UTC
    'periodic-facility-sync': {
        'task': 'periodic_facility_sync',  # Task name from @celery_app.task decorator
        'schedule': crontab(hour=2, minute=0),
    },
    # News monitoring - every 6 hours
    'monitor-news-articles': {
        'task': 'monitor_news_articles',  # Task name from @shared_task decorator
        'schedule': crontab(minute=0, hour='*/6'),
        'kwargs': {'days': 7, 'limit': 50}
    },
    # Dataset ingestion - daily at 3 AM UTC (only ingests new images)
    'ingest-datasets': {
        'task': 'ingest_datasets',
        'schedule': crontab(hour=3, minute=0),
        'kwargs': {'dataset': 'all', 'skip_existing': True}
    },
}

celery_app.conf.timezone = 'UTC'


def get_integration_service() -> IntegrationService:
    """Get integration service with API clients"""
    session = SessionLocal()
    
    # Get API clients from factory
    clients = get_api_clients()
    
    return IntegrationService(
        session=session,
        usda_client=clients.get("usda"),
        cites_client=clients.get("cites"),
        usfws_client=clients.get("usfws")
    )


@celery_app.task(name="sync_facility_usda")
def sync_facility_usda_task(
    license_number: str,
    facility_id: Optional[str] = None,
    investigation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Background task to sync facility data from USDA
    
    Args:
        license_number: USDA license number
        facility_id: Optional facility ID to update
        investigation_id: Optional investigation ID for evidence linking
    
    Returns:
        Task result with sync status
    """
    import asyncio
    job_id = sync_facility_usda_task.request.id
    logger.info("Starting USDA facility sync", job_id=job_id, license_number=license_number)
    
    try:
        with with_db_session() as session:
            job = BackgroundJob(
                job_id=safe_uuid(job_id),
                job_type="sync_facility_usda",
                status="running",
                parameters={"license_number": license_number}
            )
            session.add(job)
            session.commit()
            
            integration_service = get_integration_service()
            integration_service.session = session
            
            # Run async function in sync context
            facility = asyncio.run(integration_service.sync_facility_from_usda(
                license_number=license_number,
                investigation_id=safe_uuid(investigation_id)
            ))
            
            if facility:
                job.status = "completed"
                job.result = {"facility_id": str(facility.facility_id), "success": True}
            else:
                job.status = "failed"
                job.result = {"success": False, "message": "No facility data found"}
            
            job.completed_at = datetime.utcnow()
            session.commit()
            
            return job.result
        
    except Exception as e:
        logger.error("USDA facility sync failed", error=str(e))
        return {"success": False, "error": str(e)}


@celery_app.task(name="sync_facility_inspections")
def sync_facility_inspections_task(
    facility_id: str,
    investigation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Background task to sync facility inspection reports
    
    Args:
        facility_id: Facility ID
        investigation_id: Optional investigation ID
    
    Returns:
        Task result with sync status
    """
    job_id = sync_facility_inspections_task.request.id
    logger.info("Starting inspection sync", job_id=job_id, facility_id=facility_id)
    
    try:
        with with_db_session() as session:
            integration_service = get_integration_service()
            integration_service.session = session
            
            import asyncio
            inspections = asyncio.run(integration_service.sync_facility_inspections(
                facility_id=parse_uuid(facility_id),
                investigation_id=safe_uuid(investigation_id)
            ))
            
            return {"success": True, "count": len(inspections), "inspections": inspections}
        
    except Exception as e:
        logger.error("Inspection sync failed", error=str(e))
        return {"success": False, "error": str(e)}


@celery_app.task(name="sync_cites_trade_records")
def sync_cites_trade_records_task(
    investigation_id: str,
    country_origin: Optional[str] = None,
    country_destination: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Background task to sync CITES trade records
    
    Args:
        investigation_id: Investigation ID
        country_origin: Origin country code
        country_destination: Destination country code
        year: Year to filter
        limit: Maximum records
    
    Returns:
        Task result with sync status
    """
    job_id = sync_cites_trade_records_task.request.id
    logger.info("Starting CITES trade sync", job_id=job_id, investigation_id=investigation_id)
    
    try:
        with with_db_session() as session:
            integration_service = get_integration_service()
            integration_service.session = session
            
            import asyncio
            records = asyncio.run(integration_service.sync_cites_trade_records(
                investigation_id=parse_uuid(investigation_id),
                country_origin=country_origin,
                country_destination=country_destination,
                year=year,
                limit=limit
            ))
            
            return {"success": True, "count": len(records), "records": records}
        
    except Exception as e:
        logger.error("CITES trade sync failed", error=str(e))
        return {"success": False, "error": str(e)}


@celery_app.task(name="sync_usfws_permits")
def sync_usfws_permits_task(
    investigation_id: str,
    permit_number: Optional[str] = None,
    applicant_name: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Background task to sync USFWS permit records
    
    Args:
        investigation_id: Investigation ID
        permit_number: Permit number to filter
        applicant_name: Applicant name to filter
        limit: Maximum records
    
    Returns:
        Task result with sync status
    """
    job_id = sync_usfws_permits_task.request.id
    logger.info("Starting USFWS permit sync", job_id=job_id, investigation_id=investigation_id)
    
    try:
        with with_db_session() as session:
            integration_service = get_integration_service()
            integration_service.session = session
            
            import asyncio
            permits = asyncio.run(integration_service.sync_usfws_permits(
                investigation_id=parse_uuid(investigation_id),
                permit_number=permit_number,
                applicant_name=applicant_name,
                limit=limit
            ))
            
            return {"success": True, "count": len(permits), "permits": permits}
        
    except Exception as e:
        logger.error("USFWS permit sync failed", error=str(e))
        return {"success": False, "error": str(e)}


@celery_app.task(name="periodic_facility_sync")
def periodic_facility_sync_task() -> Dict[str, Any]:
    """
    Periodic task to sync all facilities with USDA data
    
    Returns:
        Task result with sync status
    """
    logger.info("Starting periodic facility sync")
    
    try:
        with with_db_session() as session:
            facilities = session.query(Facility).filter(
                Facility.usda_license.isnot(None)
            ).all()
            
            integration_service = get_integration_service()
            integration_service.session = session
            
            import asyncio
            synced = 0
            for facility in facilities:
                try:
                    asyncio.run(integration_service.sync_facility_from_usda(facility.usda_license))
                    synced += 1
                except Exception as e:
                    logger.warning("Failed to sync facility", facility_id=str(facility.facility_id), error=str(e))
            
            return {"success": True, "synced": synced, "total": len(facilities)}
        
    except Exception as e:
        logger.error("Periodic facility sync failed", error=str(e))
        return {"success": False, "error": str(e)}


@celery_app.task(name="download_atrw_dataset")
def download_atrw_dataset_task(dataset_dir: str, force: bool = False) -> Dict[str, Any]:
    """
    Background task to download ATRW dataset
    
    Args:
        dataset_dir: Directory to store dataset
        force: Force download even if exists
    
    Returns:
        Task result with download status
    """
    logger.info("Starting ATRW dataset download", dataset_dir=dataset_dir)
    
    try:
        import asyncio
        manager = ATRWDatasetManager(dataset_dir=dataset_dir)
        result = asyncio.run(manager.download_dataset(force=force))
        return result
        
    except Exception as e:
        logger.error("ATRW dataset download failed", error=str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task(name="ingest_datasets")
def ingest_datasets_task(
    dataset: str = "all",
    skip_existing: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Background task to ingest datasets into database
    
    Args:
        dataset: Dataset to ingest ('atrw', 'metawild', 'wildlife_datasets', 'individual_animal_reid', 'all')
        skip_existing: Skip images that already exist
        dry_run: Don't write to database (for testing)
    
    Returns:
        Task result with ingestion status
    """
    job_id = ingest_datasets_task.request.id
    logger.info("Starting dataset ingestion", job_id=job_id, dataset=dataset)
    
    try:
        import asyncio
        import sys
        from pathlib import Path
        
        # Add scripts to path
        scripts_path = Path(__file__).parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        from scripts.ingest_datasets import DatasetIngester
        
        ingester = DatasetIngester(dry_run=dry_run, skip_existing=skip_existing)
        
        if dataset == "all":
            results = asyncio.run(ingester.ingest_all_datasets())
        else:
            dataset_paths = ingester.get_dataset_paths()
            if dataset not in dataset_paths:
                return {"success": False, "error": f"Unknown dataset: {dataset}"}
            
            dataset_path = dataset_paths[dataset]
            
            if dataset == 'atrw':
                results = {dataset: asyncio.run(ingester.ingest_atrw_dataset(dataset_path))}
            elif dataset == 'metawild':
                results = {dataset: asyncio.run(ingester.ingest_metawild_dataset(dataset_path))}
            elif dataset == 'wildlife_datasets':
                results = {dataset: asyncio.run(ingester.ingest_wildlife_datasets(dataset_path))}
            elif dataset == 'individual_animal_reid':
                results = {dataset: asyncio.run(ingester.ingest_individual_animal_reid(dataset_path))}
            else:
                return {"success": False, "error": f"Unknown dataset: {dataset}"}
        
        stats = ingester.get_stats()
        
        return {
            "success": True,
            "results": results,
            "stats": stats
        }
        
    except Exception as e:
        logger.error("Dataset ingestion failed", error=str(e), exc_info=True)
        return {"success": False, "error": str(e)}


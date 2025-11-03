"""Background job definitions"""

try:
    from backend.jobs.crawl_job import crawl_facility_social_media
except ImportError:
    crawl_facility_social_media = None

from backend.jobs.data_sync_jobs import (
    celery_app,
    sync_facility_usda_task,
    sync_facility_inspections_task,
    sync_cites_trade_records_task,
    sync_usfws_permits_task,
    periodic_facility_sync_task,
    download_atrw_dataset_task,
    ingest_datasets_task,
)

try:
    from backend.jobs.news_monitoring_job import monitor_news_articles
except ImportError:
    monitor_news_articles = None

__all__ = [
    "celery_app",
    "crawl_facility_social_media",
    "sync_facility_usda_task",
    "sync_facility_inspections_task",
    "sync_cites_trade_records_task",
    "sync_usfws_permits_task",
    "periodic_facility_sync_task",
    "download_atrw_dataset_task",
    "ingest_datasets_task",
    "monitor_news_articles",
]
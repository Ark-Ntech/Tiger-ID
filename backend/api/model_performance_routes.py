"""
Model performance monitoring API routes.

Tracks and reports model inference times, accuracy metrics, and performance statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from backend.database import get_db
from backend.auth.auth import get_current_user
from backend.services.model_performance_service import ModelPerformanceService
from backend.utils.response_models import SuccessResponse
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/model-performance", tags=["model-performance"])


@router.get("/metrics")
async def get_model_metrics(
    model_name: Optional[str] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get model performance metrics.
    
    Returns:
    - Inference times (avg, min, max, p95, p99)
    - Accuracy metrics
    - Request counts
    - Error rates
    """
    try:
        performance_service = ModelPerformanceService(db)
        
        metrics = await performance_service.get_metrics(
            model_name=model_name,
            start_date=start_date,
            end_date=end_date
        )
        
        return SuccessResponse(data=metrics)
        
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard")
async def get_performance_dashboard(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get performance dashboard data.
    
    Returns aggregated metrics for all models over the specified time period.
    """
    try:
        performance_service = ModelPerformanceService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        dashboard_data = await performance_service.get_dashboard(
            start_date=start_date,
            end_date=end_date
        )
        
        return SuccessResponse(data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models")
async def get_model_list(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get list of all models with their current status.
    """
    try:
        performance_service = ModelPerformanceService(db)
        
        models = await performance_service.get_model_list()
        
        return SuccessResponse(data=models)
        
    except Exception as e:
        logger.error(f"Error getting model list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


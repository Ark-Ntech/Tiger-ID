"""API routes for model version management"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel

from backend.database import get_db
from backend.database.models import User, ModelType
from backend.auth.auth import get_current_user
from backend.services.model_version_service import ModelVersionService
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/model-versions", tags=["model-versions"])


# Request/Response models
class CreateModelVersionRequest(BaseModel):
    model_name: str
    model_type: str  # 'detection', 'reid', 'pose'
    version: str
    path: str
    training_data_hash: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    is_active: bool = False


class UpdateMetricsRequest(BaseModel):
    metrics: Dict[str, Any]
    merge: bool = True


class SetupABTestRequest(BaseModel):
    model_name: str
    control_version_id: UUID
    treatment_version_id: UUID
    traffic_split: float = 0.5


class StopABTestRequest(BaseModel):
    model_name: str
    winning_version_id: Optional[UUID] = None


@router.post("", response_model=Dict[str, Any])
async def create_model_version(
    request: CreateModelVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new model version"""
    try:
        # Validate model_type
        try:
            model_type = ModelType(request.model_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model_type: {request.model_type}. Must be one of: {[e.value for e in ModelType]}"
            )
        
        service = ModelVersionService(db)
        model_version = service.create_version(
            model_name=request.model_name,
            model_type=model_type,
            version=request.version,
            path=request.path,
            training_data_hash=request.training_data_hash,
            metrics=request.metrics,
            is_active=request.is_active
        )
        
        return {
            "success": True,
            "data": {
                "model_id": str(model_version.model_id),
                "model_name": model_version.model_name,
                "model_type": model_version.model_type.value,
                "version": model_version.version,
                "path": model_version.path,
                "is_active": model_version.is_active,
                "created_at": model_version.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error creating model version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=Dict[str, Any])
async def list_model_versions(
    model_name: Optional[str] = None,
    model_type: Optional[str] = None,
    include_inactive: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List model versions"""
    try:
        service = ModelVersionService(db)
        
        model_type_enum = None
        if model_type:
            try:
                model_type_enum = ModelType(model_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model_type: {model_type}"
                )
        
        versions = service.list_versions(
            model_name=model_name,
            model_type=model_type_enum,
            include_inactive=include_inactive
        )
        
        return {
            "success": True,
            "data": [
                {
                    "model_id": str(v.model_id),
                    "model_name": v.model_name,
                    "model_type": v.model_type.value,
                    "version": v.version,
                    "path": v.path,
                    "is_active": v.is_active,
                    "metrics": v.metrics or {},
                    "created_at": v.created_at.isoformat()
                }
                for v in versions
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing model versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=Dict[str, Any])
async def get_model_version(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific model version"""
    try:
        service = ModelVersionService(db)
        model_version = service.get_version(model_id)
        
        if not model_version:
            raise HTTPException(status_code=404, detail="Model version not found")
        
        statistics = service.get_version_statistics(model_id)
        
        return {
            "success": True,
            "data": {
                "model_id": str(model_version.model_id),
                "model_name": model_version.model_name,
                "model_type": model_version.model_type.value,
                "version": model_version.version,
                "path": model_version.path,
                "training_data_hash": model_version.training_data_hash,
                "metrics": model_version.metrics or {},
                "is_active": model_version.is_active,
                "created_at": model_version.created_at.isoformat(),
                "statistics": statistics
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/activate", response_model=Dict[str, Any])
async def activate_model_version(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate a model version (deactivates other versions of the same model)"""
    try:
        service = ModelVersionService(db)
        model_version = service.activate_version(model_id)
        
        return {
            "success": True,
            "data": {
                "model_id": str(model_version.model_id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating model version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_model_version(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a model version"""
    try:
        service = ModelVersionService(db)
        model_version = service.deactivate_version(model_id)
        
        return {
            "success": True,
            "data": {
                "model_id": str(model_version.model_id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating model version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/rollback", response_model=Dict[str, Any])
async def rollback_to_version(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rollback to a previous model version"""
    try:
        service = ModelVersionService(db)
        model_version = service.rollback_to_version(model_id)
        
        return {
            "success": True,
            "data": {
                "model_id": str(model_version.model_id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "message": f"Rolled back to version {model_version.version}"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error rolling back model version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/setup", response_model=Dict[str, Any])
async def setup_ab_test(
    request: SetupABTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set up A/B testing between two model versions"""
    try:
        if not 0 <= request.traffic_split <= 1:
            raise HTTPException(
                status_code=400,
                detail="traffic_split must be between 0 and 1"
            )
        
        service = ModelVersionService(db)
        ab_config = service.setup_ab_test(
            model_name=request.model_name,
            control_version_id=request.control_version_id,
            treatment_version_id=request.treatment_version_id,
            traffic_split=request.traffic_split
        )
        
        return {
            "success": True,
            "data": ab_config
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting up A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/stop", response_model=Dict[str, Any])
async def stop_ab_test(
    request: StopABTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop A/B test and activate winning version"""
    try:
        service = ModelVersionService(db)
        model_version = service.stop_ab_test(
            model_name=request.model_name,
            winning_version_id=request.winning_version_id
        )
        
        return {
            "success": True,
            "data": {
                "model_id": str(model_version.model_id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "message": "A/B test stopped"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error stopping A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/{model_name}", response_model=Dict[str, Any])
async def get_ab_test_config(
    model_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current A/B test configuration for a model"""
    try:
        service = ModelVersionService(db)
        ab_config = service.get_ab_test_config(model_name)
        
        if not ab_config:
            return {
                "success": True,
                "data": None,
                "message": "No active A/B test for this model"
            }
        
        return {
            "success": True,
            "data": ab_config
        }
    except Exception as e:
        logger.error(f"Error getting A/B test config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{model_id}/metrics", response_model=Dict[str, Any])
async def update_metrics(
    model_id: UUID,
    request: UpdateMetricsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update model version metrics"""
    try:
        service = ModelVersionService(db)
        model_version = service.update_metrics(
            model_id=model_id,
            metrics=request.metrics,
            merge=request.merge
        )
        
        return {
            "success": True,
            "data": {
                "model_id": str(model_version.model_id),
                "metrics": model_version.metrics
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/statistics", response_model=Dict[str, Any])
async def get_version_statistics(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a model version"""
    try:
        service = ModelVersionService(db)
        statistics = service.get_version_statistics(model_id)
        
        return {
            "success": True,
            "data": statistics
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting version statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


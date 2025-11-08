"""
Fine-tuning API routes for model training.

Allows users to fine-tune models with selected tiger images and training parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from backend.database import get_db
from backend.auth.auth import get_current_user
from backend.services.finetuning_service import FineTuningService
from backend.utils.response_models import SuccessResponse
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/finetuning", tags=["finetuning"])


# Request models
class FineTuningRequest(BaseModel):
    model_name: str = Field(..., description="Model to fine-tune (tiger_reid, wildlife_tools, etc.)")
    tiger_ids: List[str] = Field(..., description="List of tiger IDs to use for training")
    epochs: int = Field(50, ge=1, le=1000, description="Number of training epochs")
    batch_size: int = Field(32, ge=1, le=128, description="Batch size for training")
    learning_rate: float = Field(0.001, ge=0.0001, le=0.1, description="Learning rate")
    validation_split: float = Field(0.2, ge=0.1, le=0.5, description="Validation split ratio")
    loss_function: str = Field("triplet", description="Loss function (triplet, contrastive, softmax)")
    description: Optional[str] = Field(None, description="Description of this fine-tuning run")


class FineTuningJobResponse(BaseModel):
    job_id: str
    model_name: str
    status: str
    progress: float
    epochs: int
    current_epoch: int
    loss: Optional[float] = None
    validation_loss: Optional[float] = None
    created_at: str
    updated_at: str


@router.post("/start")
async def start_finetuning(
    request: FineTuningRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Start a fine-tuning job for a model.
    
    Creates a training job that will:
    1. Collect images from specified tigers
    2. Prepare training/validation splits
    3. Train the model on Modal
    4. Save updated weights to Modal volume
    """
    try:
        finetuning_service = FineTuningService(db)
        
        # Start fine-tuning job
        job = await finetuning_service.start_finetuning_job(
            model_name=request.model_name,
            tiger_ids=[UUID(tid) for tid in request.tiger_ids],
            epochs=request.epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            validation_split=request.validation_split,
            loss_function=request.loss_function,
            description=request.description,
            user_id=current_user.user_id
        )
        
        return SuccessResponse(
            message="Fine-tuning job started",
            data={
                "job_id": str(job.job_id),
                "status": job.status,
                "model_name": job.model_name,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting fine-tuning job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs")
async def list_finetuning_jobs(
    model_name: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List fine-tuning jobs.
    
    Supports filtering by model_name and status.
    """
    try:
        finetuning_service = FineTuningService(db)
        
        jobs = await finetuning_service.list_jobs(
            user_id=current_user.user_id,
            model_name=model_name,
            status=status,
            page=page,
            page_size=page_size
        )
        
        return SuccessResponse(data=jobs)
        
    except Exception as e:
        logger.error(f"Error listing fine-tuning jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs/{job_id}")
async def get_finetuning_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get fine-tuning job details and progress.
    """
    try:
        finetuning_service = FineTuningService(db)
        
        job = await finetuning_service.get_job(job_id, current_user.user_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return SuccessResponse(data=job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fine-tuning job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/jobs/{job_id}/cancel")
async def cancel_finetuning_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cancel a running fine-tuning job.
    """
    try:
        finetuning_service = FineTuningService(db)
        
        job = await finetuning_service.cancel_job(job_id, current_user.user_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return SuccessResponse(
            message="Fine-tuning job cancelled",
            data={"job_id": str(job_id), "status": job.status}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling fine-tuning job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/available-tigers")
async def get_available_tigers_for_training(
    min_images: int = 5,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get list of tigers available for training (with sufficient images).
    """
    try:
        from backend.database.models import Tiger, TigerImage
        
        # Get tigers with at least min_images
        tigers = db.query(Tiger).join(TigerImage).group_by(Tiger.tiger_id).having(
            db.func.count(TigerImage.image_id) >= min_images
        ).all()
        
        tiger_list = []
        for tiger in tigers:
            image_count = db.query(TigerImage).filter(
                TigerImage.tiger_id == tiger.tiger_id
            ).count()
            
            tiger_list.append({
                "tiger_id": str(tiger.tiger_id),
                "name": tiger.name,
                "alias": tiger.alias,
                "image_count": image_count,
                "status": tiger.status.value if hasattr(tiger.status, 'value') else str(tiger.status)
            })
        
        return SuccessResponse(data=tiger_list)
        
    except Exception as e:
        logger.error(f"Error getting available tigers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


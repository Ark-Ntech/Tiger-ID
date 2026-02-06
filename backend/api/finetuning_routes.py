"""
Fine-tuning API routes for model training.

Allows users to fine-tune the 6-model ReID ensemble with selected tiger images
and training parameters. Training runs on Modal GPUs using PyTorch with metric
learning losses (triplet, contrastive, ArcFace, circle).

Note: This uses PyTorch/timm for computer vision fine-tuning, NOT LLM fine-tuning
libraries like Unsloth or LLaMA-Factory (which are for language models only).
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from backend.database import get_db
from backend.auth.auth import get_current_user
from backend.services.finetuning_service import FineTuningService, MODEL_REGISTRY, LossFunction
from backend.utils.response_models import SuccessResponse
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/finetuning", tags=["finetuning"])

# Valid model names and loss functions derived from the service registry
VALID_MODEL_NAMES = list(MODEL_REGISTRY.keys())
VALID_LOSS_FUNCTIONS = [lf.value for lf in LossFunction]


# Request models
class FineTuningRequest(BaseModel):
    model_name: str = Field(
        ...,
        description=(
            "Model to fine-tune. One of: wildlife_tools, cvwc2019_reid, transreid, "
            "megadescriptor_b, tiger_reid, rapid_reid"
        ),
    )
    tiger_ids: List[str] = Field(
        ...,
        min_length=3,
        description="List of tiger IDs to use for training (minimum 3 for metric learning)",
    )
    epochs: int = Field(50, ge=1, le=1000, description="Number of training epochs")
    batch_size: int = Field(32, ge=1, le=128, description="Batch size for training")
    learning_rate: float = Field(0.001, ge=0.0001, le=0.1, description="Learning rate")
    validation_split: float = Field(0.2, ge=0.1, le=0.5, description="Fraction held out for testing")
    loss_function: str = Field(
        "triplet",
        description="Loss function: triplet, contrastive, softmax, arcface, or circle",
    )
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
    best_validation_loss: Optional[float] = None
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

    Returns tigers that have at least `min_images` photos in the database,
    making them suitable for inclusion in a fine-tuning training set.
    """
    try:
        from sqlalchemy import func
        from backend.database.models import Tiger, TigerImage

        # Get tigers with at least min_images
        tigers = db.query(Tiger).join(TigerImage).group_by(Tiger.tiger_id).having(
            func.count(TigerImage.image_id) >= min_images
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


@router.get("/models")
async def get_available_models(
    model_name: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Get information about models available for fine-tuning.

    Returns architecture details, default hyperparameters, supported loss
    functions, and GPU requirements for each of the 6 ensemble models.

    Query params:
        model_name: Optional. If provided, returns info for that model only.
    """
    try:
        # Use a temporary service instance (no DB needed for model info)
        from backend.services.finetuning_service import MODEL_REGISTRY, LossFunction, _get_loss_config

        if model_name:
            if model_name not in MODEL_REGISTRY:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown model: {model_name}. Valid: {VALID_MODEL_NAMES}"
                )
            config = MODEL_REGISTRY[model_name]
            return SuccessResponse(data={
                "model": model_name,
                "config": {
                    "description": config["description"],
                    "architecture": config["architecture"],
                    "backbone": config["backbone"],
                    "embedding_dim": config["embedding_dim"],
                    "input_size": list(config["input_size"]),
                    "weight_in_ensemble": config["weight_in_ensemble"],
                    "default_lr": config["default_lr"],
                    "default_batch_size": config["default_batch_size"],
                    "gpu_requirement": config["gpu_requirement"],
                    "freeze_layers": config["freeze_layers"],
                    "uses_timm": config["timm_model"],
                },
            })

        # Return all models
        models_info = {}
        for name, config in MODEL_REGISTRY.items():
            models_info[name] = {
                "description": config["description"],
                "architecture": config["architecture"],
                "embedding_dim": config["embedding_dim"],
                "input_size": list(config["input_size"]),
                "weight_in_ensemble": config["weight_in_ensemble"],
                "default_lr": config["default_lr"],
                "default_batch_size": config["default_batch_size"],
                "gpu_requirement": config["gpu_requirement"],
            }

        return SuccessResponse(data={
            "models": models_info,
            "supported_loss_functions": VALID_LOSS_FUNCTIONS,
            "notes": {
                "framework": "PyTorch with timm and torchvision",
                "training_approach": (
                    "Metric learning (triplet/contrastive/ArcFace/circle) for "
                    "vision-based tiger re-identification. Uses PyTorch training "
                    "loops, NOT LLM fine-tuning libraries."
                ),
                "compute": "Modal GPU (T4 or A100 depending on model)",
            },
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


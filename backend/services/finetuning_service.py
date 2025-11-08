"""
Fine-tuning service for model training.

Handles fine-tuning jobs, training data preparation, and Modal integration.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum

from backend.database.models import Tiger, TigerImage
from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client

logger = get_logger(__name__)


class FineTuningJobStatus(str, Enum):
    pending = "pending"
    preparing = "preparing"
    training = "training"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class FineTuningJob:
    """Fine-tuning job model (in-memory for now, should be persisted to DB)"""
    
    def __init__(
        self,
        job_id: UUID,
        model_name: str,
        tiger_ids: List[UUID],
        epochs: int,
        batch_size: int,
        learning_rate: float,
        validation_split: float,
        loss_function: str,
        user_id: UUID,
        description: Optional[str] = None
    ):
        self.job_id = job_id
        self.model_name = model_name
        self.tiger_ids = tiger_ids
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.validation_split = validation_split
        self.loss_function = loss_function
        self.user_id = user_id
        self.description = description
        self.status = FineTuningJobStatus.pending
        self.progress = 0.0
        self.current_epoch = 0
        self.loss = None
        self.validation_loss = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.error_message = None


class FineTuningService:
    """Service for managing fine-tuning jobs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.modal_client = get_modal_client()
        self._jobs: Dict[UUID, FineTuningJob] = {}  # In-memory storage, should use DB
    
    async def start_finetuning_job(
        self,
        model_name: str,
        tiger_ids: List[UUID],
        epochs: int,
        batch_size: int,
        learning_rate: float,
        validation_split: float,
        loss_function: str,
        user_id: UUID,
        description: Optional[str] = None
    ) -> FineTuningJob:
        """
        Start a fine-tuning job.
        
        Args:
            model_name: Model to fine-tune
            tiger_ids: List of tiger IDs to use for training
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            validation_split: Validation split ratio
            loss_function: Loss function to use
            user_id: User ID who started the job
            description: Optional description
            
        Returns:
            FineTuningJob instance
        """
        # Validate model name
        valid_models = ['tiger_reid', 'wildlife_tools', 'rapid', 'cvwc2019']
        if model_name not in valid_models:
            raise ValueError(f"Invalid model name. Must be one of: {valid_models}")
        
        # Validate tigers exist and have images
        for tiger_id in tiger_ids:
            tiger = self.db.query(Tiger).filter(Tiger.tiger_id == tiger_id).first()
            if not tiger:
                raise ValueError(f"Tiger {tiger_id} not found")
            
            image_count = self.db.query(TigerImage).filter(
                TigerImage.tiger_id == tiger_id
            ).count()
            
            if image_count < 5:
                raise ValueError(f"Tiger {tiger_id} has insufficient images ({image_count}). Minimum 5 required.")
        
        # Create job
        job_id = uuid4()
        job = FineTuningJob(
            job_id=job_id,
            model_name=model_name,
            tiger_ids=tiger_ids,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            validation_split=validation_split,
            loss_function=loss_function,
            user_id=user_id,
            description=description
        )
        
        self._jobs[job_id] = job
        
        # Start training asynchronously (in real implementation, use background task)
        # For now, we'll just mark it as preparing
        job.status = FineTuningJobStatus.preparing
        job.updated_at = datetime.now()
        
        logger.info(f"Started fine-tuning job {job_id} for model {model_name} with {len(tiger_ids)} tigers")
        
        # TODO: Actually start training on Modal
        # This would involve:
        # 1. Collecting images from tigers
        # 2. Preparing training/validation splits
        # 3. Calling Modal function to start training
        # 4. Monitoring progress
        
        return job
    
    async def get_job(self, job_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job details"""
        job = self._jobs.get(job_id)
        
        if not job:
            return None
        
        if job.user_id != user_id:
            return None  # User doesn't have access
        
        return {
            "job_id": str(job.job_id),
            "model_name": job.model_name,
            "status": job.status.value,
            "progress": job.progress,
            "epochs": job.epochs,
            "current_epoch": job.current_epoch,
            "loss": job.loss,
            "validation_loss": job.validation_loss,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "description": job.description,
            "tiger_ids": [str(tid) for tid in job.tiger_ids],
            "error_message": job.error_message
        }
    
    async def list_jobs(
        self,
        user_id: UUID,
        model_name: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List jobs for user"""
        user_jobs = [
            job for job in self._jobs.values()
            if job.user_id == user_id
        ]
        
        # Filter by model_name
        if model_name:
            user_jobs = [job for job in user_jobs if job.model_name == model_name]
        
        # Filter by status
        if status:
            user_jobs = [job for job in user_jobs if job.status.value == status]
        
        # Sort by created_at descending
        user_jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        # Paginate
        total = len(user_jobs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_jobs = user_jobs[start:end]
        
        return {
            "jobs": [
                {
                    "job_id": str(job.job_id),
                    "model_name": job.model_name,
                    "status": job.status.value,
                    "progress": job.progress,
                    "epochs": job.epochs,
                    "current_epoch": job.current_epoch,
                    "created_at": job.created_at.isoformat(),
                    "description": job.description
                }
                for job in paginated_jobs
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def cancel_job(self, job_id: UUID, user_id: UUID) -> Optional[FineTuningJob]:
        """Cancel a job"""
        job = self._jobs.get(job_id)
        
        if not job:
            return None
        
        if job.user_id != user_id:
            return None
        
        if job.status in [FineTuningJobStatus.completed, FineTuningJobStatus.failed, FineTuningJobStatus.cancelled]:
            return job  # Already finished
        
        job.status = FineTuningJobStatus.cancelled
        job.updated_at = datetime.now()
        
        logger.info(f"Cancelled fine-tuning job {job_id}")
        
        # TODO: Actually cancel training on Modal
        
        return job


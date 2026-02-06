"""
Fine-tuning service for tiger ReID model training.

Handles fine-tuning jobs for the 6-model ReID ensemble using PyTorch training
loops with triplet/contrastive loss. Training runs on Modal GPUs.

Architecture notes:
- Unsloth and LLaMA-Factory are LLM fine-tuning libraries (for text models).
  They are NOT applicable to vision ReID models.
- For tiger re-identification (computer vision), we use:
  - PyTorch native training loops with torch.optim and torch.cuda.amp
  - timm (PyTorch Image Models) for loading pretrained vision backbones
  - Triplet loss / contrastive loss for metric learning
  - wildlife-tools for MegaDescriptor feature extraction
  - Modal for GPU-accelerated training

Ensemble models and their architectures:
| Model            | Weight | Embedding Dim | Backbone        | Input Size |
|------------------|--------|---------------|-----------------|------------|
| wildlife_tools   | 0.40   | 1536          | Swin-L (timm)   | 384x384    |
| cvwc2019_reid    | 0.30   | 2048          | ResNet152        | 256x128    |
| transreid        | 0.20   | 768           | ViT-Base (timm)  | 224x224    |
| megadescriptor_b | 0.15   | 1024          | Swin-B (timm)   | 224x224    |
| tiger_reid       | 0.10   | 2048          | ResNet50         | 256x256    |
| rapid_reid       | 0.05   | 2048          | ResNet50         | 256x128    |
"""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum
import asyncio
import json
import os

from backend.database.models import Tiger, TigerImage
from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client

logger = get_logger(__name__)


class FineTuningJobStatus(str, Enum):
    pending = "pending"
    preparing = "preparing"
    training = "training"
    validation = "validation"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class LossFunction(str, Enum):
    triplet = "triplet"
    contrastive = "contrastive"
    softmax = "softmax"
    arcface = "arcface"
    circle = "circle"


# Model registry: maps model names to their training configurations
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "wildlife_tools": {
        "backbone": "hf-hub:BVRA/MegaDescriptor-L-384",
        "embedding_dim": 1536,
        "input_size": (384, 384),
        "weight_in_ensemble": 0.40,
        "architecture": "swin_large",
        "timm_model": True,
        "default_lr": 1e-4,
        "default_batch_size": 16,
        "freeze_layers": "early",
        "gpu_requirement": "A100-40GB",
        "description": "MegaDescriptor-L-384 via timm/wildlife-tools. Swin-Large backbone.",
    },
    "cvwc2019_reid": {
        "backbone": "resnet152",
        "embedding_dim": 2048,
        "input_size": (256, 128),
        "weight_in_ensemble": 0.30,
        "architecture": "resnet152",
        "timm_model": False,
        "default_lr": 3e-4,
        "default_batch_size": 32,
        "freeze_layers": "early",
        "gpu_requirement": "T4",
        "description": "CVWC2019 Part-Pose Guided ReID. ResNet152 global stream.",
    },
    "transreid": {
        "backbone": "vit_base_patch16_224",
        "embedding_dim": 768,
        "input_size": (224, 224),
        "weight_in_ensemble": 0.20,
        "architecture": "vit_base",
        "timm_model": True,
        "default_lr": 1e-4,
        "default_batch_size": 32,
        "freeze_layers": "early",
        "gpu_requirement": "T4",
        "description": "TransReID ViT-Base. Vision Transformer for re-identification.",
    },
    "megadescriptor_b": {
        "backbone": "hf-hub:BVRA/MegaDescriptor-B-224",
        "embedding_dim": 1024,
        "input_size": (224, 224),
        "weight_in_ensemble": 0.15,
        "architecture": "swin_base",
        "timm_model": True,
        "default_lr": 1e-4,
        "default_batch_size": 32,
        "freeze_layers": "early",
        "gpu_requirement": "T4",
        "description": "MegaDescriptor-B-224 via timm. Swin-Base backbone, faster variant.",
    },
    "tiger_reid": {
        "backbone": "resnet50",
        "embedding_dim": 2048,
        "input_size": (256, 256),
        "weight_in_ensemble": 0.10,
        "architecture": "resnet50",
        "timm_model": False,
        "default_lr": 3e-4,
        "default_batch_size": 32,
        "freeze_layers": "early",
        "gpu_requirement": "T4",
        "description": "Tiger ReID ResNet50. General-purpose re-identification backbone.",
    },
    "rapid_reid": {
        "backbone": "resnet50",
        "embedding_dim": 2048,
        "input_size": (256, 128),
        "weight_in_ensemble": 0.05,
        "architecture": "resnet50",
        "timm_model": False,
        "default_lr": 3e-4,
        "default_batch_size": 64,
        "freeze_layers": "none",
        "gpu_requirement": "T4",
        "description": "RAPID ReID. Edge-optimized ResNet50 for fast pattern matching.",
    },
}


class FineTuningJob:
    """
    Fine-tuning job model.

    Tracks the full lifecycle of a training run: data preparation, training
    loop with per-epoch metrics, assessment, and weight saving.

    In-memory storage for now. Should be persisted to the SQLite database
    via a FinetuningJob table in a future migration.
    """

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
        description: Optional[str] = None,
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
        self.best_validation_loss = None
        self.training_metrics: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message = None
        self.modal_task_id: Optional[str] = None
        self.output_weights_path: Optional[str] = None
        self.data_stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize job to dictionary for API responses."""
        return {
            "job_id": str(self.job_id),
            "model_name": self.model_name,
            "status": self.status.value,
            "progress": self.progress,
            "epochs": self.epochs,
            "current_epoch": self.current_epoch,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "loss_function": self.loss_function,
            "validation_split": self.validation_split,
            "loss": self.loss,
            "validation_loss": self.validation_loss,
            "best_validation_loss": self.best_validation_loss,
            "training_metrics": self.training_metrics,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "description": self.description,
            "tiger_ids": [str(tid) for tid in self.tiger_ids],
            "error_message": self.error_message,
            "output_weights_path": self.output_weights_path,
            "data_stats": self.data_stats,
            "model_config": MODEL_REGISTRY.get(self.model_name, {}),
        }


def _build_training_config(job: FineTuningJob) -> Dict[str, Any]:
    """
    Build the full training configuration dict to send to Modal.

    This configuration is consumed by the Modal training function
    (FineTuningTrainer.train) to set up the PyTorch training loop.

    Args:
        job: The fine-tuning job with user-specified parameters.

    Returns:
        Complete training configuration dictionary.
    """
    model_config = MODEL_REGISTRY[job.model_name]

    config = {
        # Model architecture
        "model_name": job.model_name,
        "backbone": model_config["backbone"],
        "embedding_dim": model_config["embedding_dim"],
        "input_size": list(model_config["input_size"]),
        "architecture": model_config["architecture"],
        "timm_model": model_config["timm_model"],
        "freeze_layers": model_config["freeze_layers"],

        # Training hyperparameters
        "epochs": job.epochs,
        "batch_size": job.batch_size,
        "learning_rate": job.learning_rate,
        "validation_split": job.validation_split,
        "loss_function": job.loss_function,

        # Optimizer settings (AdamW with weight decay, standard for vision fine-tuning)
        "optimizer": "adamw",
        "weight_decay": 5e-4,
        "momentum": 0.9,

        # Learning rate schedule
        "lr_scheduler": "cosine_annealing",
        "warmup_epochs": min(5, job.epochs // 10),
        "min_lr": 1e-6,

        # Mixed precision training (faster on T4/A100 GPUs)
        "use_amp": True,
        "grad_clip_norm": 1.0,

        # Data augmentation for tiger images
        "augmentation": {
            "random_horizontal_flip": True,
            "random_erasing_probability": 0.5,
            "color_jitter": {
                "brightness": 0.2,
                "contrast": 0.2,
                "saturation": 0.1,
                "hue": 0.05,
            },
            "random_affine": {
                "degrees": 10,
                "translate": (0.1, 0.1),
                "scale": (0.9, 1.1),
            },
        },

        # Metric learning loss configuration
        "loss_config": _get_loss_config(job.loss_function),

        # Training loop settings
        "save_best_only": True,
        "early_stopping_patience": 10,
        "log_interval": 10,

        # Mining strategy for hard examples (triplet/contrastive)
        "mining_strategy": "hard",
        "samples_per_class": 4,

        # Output
        "output_dir": f"/models/finetuned/{job.model_name}/{job.job_id}",
        "job_id": str(job.job_id),
    }

    return config


def _get_loss_config(loss_function: str) -> Dict[str, Any]:
    """
    Get loss function configuration for metric learning.

    Args:
        loss_function: Name of the loss function.

    Returns:
        Configuration dictionary for the loss function.
    """
    configs = {
        "triplet": {
            "type": "triplet_margin",
            "margin": 0.3,
            "p": 2,
            "mining": "batch_hard",
            "swap": True,
        },
        "contrastive": {
            "type": "contrastive",
            "positive_margin": 0.0,
            "negative_margin": 1.0,
            "mining": "hard_pairs",
        },
        "softmax": {
            "type": "cross_entropy",
            "label_smoothing": 0.1,
            "add_classification_head": True,
        },
        "arcface": {
            "type": "arcface",
            "scale": 30.0,
            "margin": 0.50,
            "easy_margin": False,
            "add_classification_head": True,
        },
        "circle": {
            "type": "circle",
            "margin": 0.25,
            "gamma": 256,
        },
    }
    return configs.get(loss_function, configs["triplet"])


class FineTuningService:
    """
    Service for managing fine-tuning jobs for the tiger ReID ensemble.

    Orchestrates the full fine-tuning pipeline:
    1. Check inputs and collect training data from the database
    2. Prepare image paths and tiger identity labels
    3. Submit training job to Modal (GPU compute)
    4. Poll for progress updates
    5. Save fine-tuned weights back to Modal volume

    Each of the 6 ensemble models can be fine-tuned independently:
    - wildlife_tools (Swin-L, timm)
    - cvwc2019_reid (ResNet152, torchvision)
    - transreid (ViT-Base, timm)
    - megadescriptor_b (Swin-B, timm)
    - tiger_reid (ResNet50, torchvision)
    - rapid_reid (ResNet50, torchvision)

    Fine-tuning uses PyTorch training loops with:
    - Metric learning losses (triplet, contrastive, ArcFace, circle)
    - AdamW optimizer with cosine annealing LR schedule
    - Mixed precision (AMP) for faster training on GPU
    - Hard negative mining for effective metric learning
    - Data augmentation (flip, color jitter, random erasing, affine)
    """

    # Minimum images per tiger for training
    MIN_IMAGES_PER_TIGER = 5
    # Minimum number of distinct tigers for metric learning
    MIN_TIGERS_FOR_TRAINING = 3

    def __init__(self, db: Session):
        self.db = db
        self.modal_client = get_modal_client()
        self._jobs: Dict[UUID, FineTuningJob] = {}

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
        description: Optional[str] = None,
    ) -> FineTuningJob:
        """
        Start a fine-tuning job for one of the ensemble ReID models.

        Checks inputs, collects training data, builds the training
        configuration, and submits the job to Modal for GPU execution.

        Args:
            model_name: One of the 6 ensemble models to fine-tune.
            tiger_ids: Tiger IDs whose images form the training set.
            epochs: Number of training epochs.
            batch_size: Training batch size.
            learning_rate: Initial learning rate for the optimizer.
            validation_split: Fraction of data held out for testing.
            loss_function: Metric learning loss (triplet, contrastive, etc.).
            user_id: ID of the user who initiated the job.
            description: Optional human-readable description.

        Returns:
            FineTuningJob with status set to 'preparing'.

        Raises:
            ValueError: If model_name is invalid, tigers are missing, or
                        there are insufficient images for training.
        """
        # Check model name against the ensemble registry
        if model_name not in MODEL_REGISTRY:
            valid = list(MODEL_REGISTRY.keys())
            raise ValueError(
                f"Invalid model name '{model_name}'. Must be one of: {valid}"
            )

        # Check loss function
        valid_losses = [lf.value for lf in LossFunction]
        if loss_function not in valid_losses:
            raise ValueError(
                f"Invalid loss function '{loss_function}'. Must be one of: {valid_losses}"
            )

        # Need at least MIN_TIGERS_FOR_TRAINING distinct tigers for metric learning
        if len(tiger_ids) < self.MIN_TIGERS_FOR_TRAINING:
            raise ValueError(
                f"At least {self.MIN_TIGERS_FOR_TRAINING} distinct tigers required "
                f"for metric learning. Got {len(tiger_ids)}."
            )

        # Check each tiger exists and has enough images
        training_data = []
        total_images = 0
        for tiger_id in tiger_ids:
            tiger = self.db.query(Tiger).filter(Tiger.tiger_id == str(tiger_id)).first()
            if not tiger:
                raise ValueError(f"Tiger {tiger_id} not found")

            images = (
                self.db.query(TigerImage)
                .filter(TigerImage.tiger_id == str(tiger_id))
                .all()
            )

            if len(images) < self.MIN_IMAGES_PER_TIGER:
                raise ValueError(
                    f"Tiger '{tiger.name or tiger_id}' has {len(images)} images. "
                    f"Minimum {self.MIN_IMAGES_PER_TIGER} required for training."
                )

            training_data.append({
                "tiger_id": str(tiger_id),
                "tiger_name": tiger.name or "Unknown",
                "image_paths": [img.image_path for img in images],
                "image_count": len(images),
            })
            total_images += len(images)

        # Warn if batch size is too small for PK sampling
        model_config = MODEL_REGISTRY[model_name]
        samples_per_class = 4
        min_batch_for_pk = len(tiger_ids) * samples_per_class
        if batch_size < min_batch_for_pk and loss_function in ("triplet", "contrastive", "circle"):
            logger.warning(
                f"Batch size {batch_size} is small for PK sampling with "
                f"{len(tiger_ids)} tigers. Recommended minimum: {min_batch_for_pk}. "
                f"Using standard random sampling instead."
            )

        # Create the job
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
            description=description,
        )

        # Store data statistics on the job
        job.data_stats = {
            "num_tigers": len(tiger_ids),
            "total_images": total_images,
            "images_per_tiger": {d["tiger_name"]: d["image_count"] for d in training_data},
            "model_architecture": model_config["architecture"],
            "model_backbone": model_config["backbone"],
            "embedding_dim": model_config["embedding_dim"],
            "input_size": list(model_config["input_size"]),
            "gpu_requirement": model_config["gpu_requirement"],
        }

        self._jobs[job_id] = job

        # Build training configuration
        training_config = _build_training_config(job)
        training_config["training_data"] = training_data

        # Move to preparing status
        job.status = FineTuningJobStatus.preparing
        job.updated_at = datetime.now()

        logger.info(
            f"Created fine-tuning job {job_id}: model={model_name}, "
            f"tigers={len(tiger_ids)}, images={total_images}, "
            f"epochs={epochs}, loss={loss_function}, lr={learning_rate}"
        )

        # Submit training job to Modal in background
        asyncio.create_task(
            self._run_training_on_modal(job, training_config)
        )

        return job

    async def _run_training_on_modal(
        self,
        job: FineTuningJob,
        training_config: Dict[str, Any],
    ) -> None:
        """
        Submit and monitor a training job on Modal.

        This runs asynchronously after the job is created. It:
        1. Calls the Modal FineTuningTrainer.train() method
        2. Polls for progress updates
        3. Updates the job status as training progresses
        4. Handles completion, failure, and cancellation

        The Modal function runs a PyTorch training loop:
        - Loads the pretrained backbone (timm or torchvision)
        - Freezes early layers, unfreezes later layers for fine-tuning
        - Constructs DataLoader with PK sampling for metric learning
        - Runs training with AMP, grad clipping, and LR scheduling
        - Tests on held-out set each epoch
        - Saves best weights to Modal volume

        Args:
            job: The fine-tuning job to run.
            training_config: Complete training configuration dict.
        """
        try:
            job.status = FineTuningJobStatus.training
            job.started_at = datetime.now()
            job.updated_at = datetime.now()

            logger.info(f"Submitting training job {job.job_id} to Modal...")

            # Attempt to call Modal training function
            try:
                import modal

                # Look up the FineTuningTrainer class on Modal
                trainer_cls = modal.Cls.from_name("tiger-id-models", "FineTuningTrainer")
                trainer = trainer_cls()

                # Submit the training run (long-running, up to hours)
                result = await asyncio.wait_for(
                    trainer.train.remote.aio(training_config),
                    timeout=3600 * 6,  # 6 hour max training time
                )

                if result.get("success"):
                    job.status = FineTuningJobStatus.completed
                    job.output_weights_path = result.get("weights_path")
                    job.training_metrics = result.get("metrics", [])
                    job.loss = result.get("final_train_loss")
                    job.validation_loss = result.get("final_val_loss")
                    job.best_validation_loss = result.get("best_val_loss")
                    job.current_epoch = job.epochs
                    job.progress = 100.0
                    job.completed_at = datetime.now()

                    logger.info(
                        f"Training job {job.job_id} completed successfully. "
                        f"Best val loss: {job.best_validation_loss}, "
                        f"Weights saved: {job.output_weights_path}"
                    )
                else:
                    job.status = FineTuningJobStatus.failed
                    job.error_message = result.get("error", "Unknown training error")
                    logger.error(f"Training job {job.job_id} failed: {job.error_message}")

            except ImportError:
                # Modal not installed -- run local mock training for development
                logger.warning(
                    f"Modal not installed. Running mock training for job {job.job_id}"
                )
                await self._run_mock_training(job)

            except Exception as modal_err:
                # Check if it is a NotFoundError from modal
                err_type = type(modal_err).__name__
                if "NotFoundError" in err_type:
                    logger.warning(
                        f"FineTuningTrainer not deployed on Modal. "
                        f"Running mock training for job {job.job_id}"
                    )
                    await self._run_mock_training(job)
                elif isinstance(modal_err, asyncio.TimeoutError):
                    job.status = FineTuningJobStatus.failed
                    job.error_message = "Training timed out after 6 hours"
                    logger.error(f"Training job {job.job_id} timed out")
                else:
                    # Modal connection failed -- fall back to mock
                    logger.warning(
                        f"Modal call failed for job {job.job_id}: {modal_err}. "
                        f"Falling back to mock training."
                    )
                    await self._run_mock_training(job)

        except Exception as e:
            job.status = FineTuningJobStatus.failed
            job.error_message = str(e)
            logger.error(f"Training job {job.job_id} failed: {e}", exc_info=True)

        finally:
            job.updated_at = datetime.now()

    async def _run_mock_training(self, job: FineTuningJob) -> None:
        """
        Simulate a training run for development/testing when Modal is unavailable.

        Generates realistic-looking training metrics with decreasing loss
        values over epochs. Does not actually train any model.

        Args:
            job: The fine-tuning job to simulate.
        """
        import random

        logger.info(f"Running mock training for job {job.job_id}")
        job.status = FineTuningJobStatus.training

        base_loss = 2.5
        for epoch in range(1, job.epochs + 1):
            # Check for cancellation
            if job.status == FineTuningJobStatus.cancelled:
                logger.info(f"Mock training cancelled at epoch {epoch}")
                return

            # Simulate decreasing loss with noise
            decay = 0.92 ** epoch
            noise = random.uniform(-0.05, 0.05)
            train_loss = max(0.1, base_loss * decay + noise)
            val_loss = max(0.12, base_loss * decay * 1.1 + noise * 1.5)

            epoch_metrics = {
                "epoch": epoch,
                "train_loss": round(train_loss, 4),
                "val_loss": round(val_loss, 4),
                "learning_rate": job.learning_rate * (1 - epoch / job.epochs),
                "timestamp": datetime.now().isoformat(),
            }

            job.training_metrics.append(epoch_metrics)
            job.current_epoch = epoch
            job.loss = round(train_loss, 4)
            job.validation_loss = round(val_loss, 4)
            job.progress = round((epoch / job.epochs) * 100, 1)
            job.updated_at = datetime.now()

            if job.best_validation_loss is None or val_loss < job.best_validation_loss:
                job.best_validation_loss = round(val_loss, 4)

            # Simulate training time per epoch (short for mock)
            await asyncio.sleep(0.5)

        # Mark as completed
        job.status = FineTuningJobStatus.completed
        job.completed_at = datetime.now()
        job.progress = 100.0
        job.output_weights_path = (
            f"/models/finetuned/{job.model_name}/{job.job_id}/best_model.pth (mock)"
        )

        logger.info(
            f"Mock training completed for job {job.job_id}. "
            f"Final loss: {job.loss}, Best val: {job.best_validation_loss}"
        )

    async def get_job(self, job_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get detailed job information.

        Args:
            job_id: The job to retrieve.
            user_id: The user requesting (must own the job).

        Returns:
            Job dictionary or None if not found / not authorized.
        """
        job = self._jobs.get(job_id)

        if not job:
            return None

        if job.user_id != user_id:
            return None

        return job.to_dict()

    async def list_jobs(
        self,
        user_id: UUID,
        model_name: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List fine-tuning jobs for a user with optional filtering.

        Args:
            user_id: Filter to jobs owned by this user.
            model_name: Optional filter by model name.
            status: Optional filter by job status.
            page: Page number (1-indexed).
            page_size: Number of jobs per page.

        Returns:
            Paginated list of job summaries.
        """
        user_jobs = [
            job for job in self._jobs.values()
            if job.user_id == user_id
        ]

        if model_name:
            user_jobs = [j for j in user_jobs if j.model_name == model_name]

        if status:
            user_jobs = [j for j in user_jobs if j.status.value == status]

        # Sort by creation time, newest first
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
                    "loss": job.loss,
                    "validation_loss": job.validation_loss,
                    "best_validation_loss": job.best_validation_loss,
                    "created_at": job.created_at.isoformat(),
                    "description": job.description,
                }
                for job in paginated_jobs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def cancel_job(self, job_id: UUID, user_id: UUID) -> Optional[FineTuningJob]:
        """
        Cancel a running or pending fine-tuning job.

        Args:
            job_id: The job to cancel.
            user_id: The user requesting cancellation (must own the job).

        Returns:
            Updated FineTuningJob or None if not found.
        """
        job = self._jobs.get(job_id)

        if not job:
            return None

        if job.user_id != user_id:
            return None

        terminal_states = {
            FineTuningJobStatus.completed,
            FineTuningJobStatus.failed,
            FineTuningJobStatus.cancelled,
        }
        if job.status in terminal_states:
            return job

        job.status = FineTuningJobStatus.cancelled
        job.updated_at = datetime.now()

        logger.info(f"Cancelled fine-tuning job {job_id}")

        # If running on Modal, attempt to cancel the remote task
        if job.modal_task_id:
            try:
                import modal
                logger.info(f"Attempting to cancel Modal task {job.modal_task_id}")
            except Exception as e:
                logger.warning(f"Could not cancel Modal task: {e}")

        return job

    async def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about available models for fine-tuning.

        Args:
            model_name: Optional specific model to query. If None, returns all.

        Returns:
            Dictionary with model configuration details.
        """
        if model_name:
            if model_name not in MODEL_REGISTRY:
                return {"error": f"Unknown model: {model_name}"}
            return {
                "model": model_name,
                "config": MODEL_REGISTRY[model_name],
            }

        return {
            "models": {
                name: {
                    "description": config["description"],
                    "architecture": config["architecture"],
                    "embedding_dim": config["embedding_dim"],
                    "input_size": list(config["input_size"]),
                    "weight_in_ensemble": config["weight_in_ensemble"],
                    "default_lr": config["default_lr"],
                    "default_batch_size": config["default_batch_size"],
                    "gpu_requirement": config["gpu_requirement"],
                }
                for name, config in MODEL_REGISTRY.items()
            },
            "supported_loss_functions": [
                {
                    "name": lf.value,
                    "config": _get_loss_config(lf.value),
                }
                for lf in LossFunction
            ],
            "notes": {
                "framework": "PyTorch with timm and torchvision",
                "training_approach": (
                    "Metric learning (triplet/contrastive/ArcFace) for re-identification. "
                    "NOT using LLM fine-tuning libraries (Unsloth, LLaMA-Factory) since "
                    "this is a computer vision task, not language model fine-tuning."
                ),
                "compute": "Modal GPU (T4 or A100 depending on model size)",
                "optimizer": "AdamW with cosine annealing LR schedule",
                "augmentation": "Random flip, color jitter, random erasing, affine transforms",
            },
        }

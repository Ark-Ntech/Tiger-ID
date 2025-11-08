"""Service for managing model versions, A/B testing, and rollback"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import json

from backend.database.models import ModelVersion, ModelInference, ModelType
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ModelVersionService:
    """Service for managing model versions with version control, A/B testing, and rollback"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_version(
        self,
        model_name: str,
        model_type: ModelType,
        version: str,
        path: str,
        training_data_hash: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        is_active: bool = False
    ) -> ModelVersion:
        """
        Create a new model version.
        
        Args:
            model_name: Name of the model (e.g., 'wildlife_tools', 'tiger_reid')
            model_type: Type of model (detection, reid, pose)
            version: Version string (e.g., '1.0.0', '2.1.3')
            path: Path to model weights/checkpoint
            training_data_hash: Hash of training data used
            metrics: Model performance metrics
            is_active: Whether this version should be active
            
        Returns:
            Created ModelVersion instance
        """
        # If this is set to active, deactivate other versions of the same model
        if is_active:
            self._deactivate_other_versions(model_name)
        
        model_version = ModelVersion(
            model_name=model_name,
            model_type=model_type,
            version=version,
            path=path,
            training_data_hash=training_data_hash,
            metrics=metrics or {},
            is_active=is_active
        )
        
        self.db.add(model_version)
        self.db.commit()
        self.db.refresh(model_version)
        
        logger.info(
            f"Created model version: {model_name} v{version}",
            model_name=model_name,
            version=version,
            is_active=is_active
        )
        
        return model_version
    
    def get_active_version(self, model_name: str) -> Optional[ModelVersion]:
        """Get the currently active version of a model"""
        return self.db.query(ModelVersion).filter(
            ModelVersion.model_name == model_name,
            ModelVersion.is_active == True
        ).first()
    
    def get_version(self, model_id: UUID) -> Optional[ModelVersion]:
        """Get a specific model version by ID"""
        return self.db.query(ModelVersion).filter(
            ModelVersion.model_id == model_id
        ).first()
    
    def list_versions(
        self,
        model_name: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        include_inactive: bool = True
    ) -> List[ModelVersion]:
        """
        List model versions with optional filters.
        
        Args:
            model_name: Filter by model name
            model_type: Filter by model type
            include_inactive: Include inactive versions
            
        Returns:
            List of ModelVersion instances
        """
        query = self.db.query(ModelVersion)
        
        if model_name:
            query = query.filter(ModelVersion.model_name == model_name)
        
        if model_type:
            query = query.filter(ModelVersion.model_type == model_type)
        
        if not include_inactive:
            query = query.filter(ModelVersion.is_active == True)
        
        return query.order_by(ModelVersion.created_at.desc()).all()
    
    def activate_version(self, model_id: UUID) -> ModelVersion:
        """
        Activate a model version (deactivates other versions of the same model).
        
        Args:
            model_id: ID of version to activate
            
        Returns:
            Activated ModelVersion instance
        """
        model_version = self.get_version(model_id)
        if not model_version:
            raise ValueError(f"Model version {model_id} not found")
        
        # Deactivate other versions of the same model
        self._deactivate_other_versions(model_version.model_name)
        
        # Activate this version
        model_version.is_active = True
        self.db.commit()
        self.db.refresh(model_version)
        
        logger.info(
            f"Activated model version: {model_version.model_name} v{model_version.version}",
            model_id=str(model_id),
            model_name=model_version.model_name,
            version=model_version.version
        )
        
        return model_version
    
    def deactivate_version(self, model_id: UUID) -> ModelVersion:
        """
        Deactivate a model version.
        
        Args:
            model_id: ID of version to deactivate
            
        Returns:
            Deactivated ModelVersion instance
        """
        model_version = self.get_version(model_id)
        if not model_version:
            raise ValueError(f"Model version {model_id} not found")
        
        model_version.is_active = False
        self.db.commit()
        self.db.refresh(model_version)
        
        logger.info(
            f"Deactivated model version: {model_version.model_name} v{model_version.version}",
            model_id=str(model_id)
        )
        
        return model_version
    
    def rollback_to_version(self, model_id: UUID) -> ModelVersion:
        """
        Rollback to a previous model version.
        
        Args:
            model_id: ID of version to rollback to
            
        Returns:
            Activated ModelVersion instance
        """
        return self.activate_version(model_id)
    
    def setup_ab_test(
        self,
        model_name: str,
        control_version_id: UUID,
        treatment_version_id: UUID,
        traffic_split: float = 0.5
    ) -> Dict[str, Any]:
        """
        Set up A/B testing between two model versions.
        
        Args:
            model_name: Name of the model
            control_version_id: ID of control version (existing/current)
            treatment_version_id: ID of treatment version (new version to test)
            traffic_split: Percentage of traffic to send to treatment (0.0-1.0)
            
        Returns:
            A/B test configuration
        """
        control_version = self.get_version(control_version_id)
        treatment_version = self.get_version(treatment_version_id)
        
        if not control_version or not treatment_version:
            raise ValueError("Both control and treatment versions must exist")
        
        if control_version.model_name != treatment_version.model_name:
            raise ValueError("Control and treatment must be versions of the same model")
        
        # Store A/B test configuration in control version's metrics
        ab_config = {
            "ab_test_active": True,
            "control_version_id": str(control_version_id),
            "treatment_version_id": str(treatment_version_id),
            "traffic_split": traffic_split,
            "started_at": datetime.utcnow().isoformat()
        }
        
        if not control_version.metrics:
            control_version.metrics = {}
        
        control_version.metrics["ab_test"] = ab_config
        self.db.commit()
        
        logger.info(
            f"Set up A/B test for {model_name}: {traffic_split*100}% to treatment",
            model_name=model_name,
            control_version=control_version.version,
            treatment_version=treatment_version.version
        )
        
        return ab_config
    
    def stop_ab_test(self, model_name: str, winning_version_id: Optional[UUID] = None) -> ModelVersion:
        """
        Stop A/B test and activate winning version.
        
        Args:
            model_name: Name of the model
            winning_version_id: ID of winning version (None to keep current)
            
        Returns:
            Activated ModelVersion instance
        """
        active_version = self.get_active_version(model_name)
        if not active_version:
            raise ValueError(f"No active version found for {model_name}")
        
        # Remove A/B test configuration
        if active_version.metrics and "ab_test" in active_version.metrics:
            del active_version.metrics["ab_test"]
            self.db.commit()
        
        # Activate winning version if specified
        if winning_version_id:
            return self.activate_version(winning_version_id)
        
        return active_version
    
    def get_ab_test_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get current A/B test configuration for a model"""
        active_version = self.get_active_version(model_name)
        if not active_version or not active_version.metrics:
            return None
        
        return active_version.metrics.get("ab_test")
    
    def update_metrics(
        self,
        model_id: UUID,
        metrics: Dict[str, Any],
        merge: bool = True
    ) -> ModelVersion:
        """
        Update model version metrics.
        
        Args:
            model_id: ID of model version
            metrics: Metrics to update
            merge: Whether to merge with existing metrics (True) or replace (False)
            
        Returns:
            Updated ModelVersion instance
        """
        model_version = self.get_version(model_id)
        if not model_version:
            raise ValueError(f"Model version {model_id} not found")
        
        if merge:
            if not model_version.metrics:
                model_version.metrics = {}
            model_version.metrics.update(metrics)
        else:
            model_version.metrics = metrics
        
        self.db.commit()
        self.db.refresh(model_version)
        
        return model_version
    
    def get_version_statistics(self, model_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for a model version (inference count, avg latency, etc.).
        
        Args:
            model_id: ID of model version
            
        Returns:
            Statistics dictionary
        """
        model_version = self.get_version(model_id)
        if not model_version:
            raise ValueError(f"Model version {model_id} not found")
        
        # Get inference statistics
        inferences = self.db.query(ModelInference).filter(
            ModelInference.model_id == model_id
        ).all()
        
        if not inferences:
            return {
                "model_id": str(model_id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "total_inferences": 0,
                "avg_latency_ms": 0,
                "avg_confidence": 0,
                "success_rate": 0
            }
        
        total = len(inferences)
        successful = sum(1 for inf in inferences if inf.confidence is not None)
        latencies = [inf.execution_time_ms for inf in inferences if inf.execution_time_ms]
        confidences = [inf.confidence for inf in inferences if inf.confidence is not None]
        
        return {
            "model_id": str(model_id),
            "model_name": model_version.model_name,
            "version": model_version.version,
            "total_inferences": total,
            "successful_inferences": successful,
            "success_rate": successful / total if total > 0 else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "min_confidence": min(confidences) if confidences else 0,
            "max_confidence": max(confidences) if confidences else 0
        }
    
    def _deactivate_other_versions(self, model_name: str) -> None:
        """Deactivate all other versions of the same model"""
        self.db.query(ModelVersion).filter(
            ModelVersion.model_name == model_name,
            ModelVersion.is_active == True
        ).update({"is_active": False})
        self.db.commit()


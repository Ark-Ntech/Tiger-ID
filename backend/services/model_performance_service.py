"""
Model performance monitoring service.

Tracks model inference times, accuracy metrics, and performance statistics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.database.models import ModelInference, ModelVersion
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ModelPerformanceService:
    """Service for monitoring model performance"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_metrics(
        self,
        model_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for models.
        
        Args:
            model_name: Filter by model name (optional)
            start_date: Start date for metrics (optional)
            end_date: End date for metrics (optional)
            
        Returns:
            Dictionary with metrics for each model
        """
        # Join with ModelVersion to get model_name
        query = self.db.query(ModelInference, ModelVersion).join(
            ModelVersion, ModelInference.model_id == ModelVersion.model_id
        )
        
        # Apply filters
        if model_name:
            query = query.filter(ModelVersion.model_name == model_name)
        
        if start_date:
            query = query.filter(ModelInference.created_at >= start_date)
        
        if end_date:
            query = query.filter(ModelInference.created_at <= end_date)
        
        # Get all logs
        results = query.all()
        
        # Group by model
        model_metrics: Dict[str, Dict[str, Any]] = {}
        
        for inference, version in results:
            model_name_key = version.model_name if version else 'unknown'
            
            if model_name_key not in model_metrics:
                model_metrics[model_name_key] = {
                    "model_name": model_name_key,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "inference_times": [],
                    "accuracy_scores": []
                }
            
            metrics = model_metrics[model_name_key]
            metrics["total_requests"] += 1
            
            if hasattr(inference, 'success') and inference.success:
                metrics["successful_requests"] += 1
            else:
                metrics["failed_requests"] += 1
            
            if hasattr(inference, 'execution_time_ms') and inference.execution_time_ms:
                metrics["inference_times"].append(inference.execution_time_ms)
            
            if hasattr(inference, 'confidence') and inference.confidence:
                metrics["accuracy_scores"].append(inference.confidence)
        
        # Calculate statistics
        result = {}
        for model_name_key, metrics in model_metrics.items():
            inference_times = metrics["inference_times"]
            accuracy_scores = metrics["accuracy_scores"]
            
            # Calculate inference time statistics
            if inference_times:
                sorted_times = sorted(inference_times)
                n = len(sorted_times)
                p95_idx = int(n * 0.95)
                p99_idx = int(n * 0.99)
                
                result[model_name_key] = {
                    "model_name": model_name_key,
                    "total_requests": metrics["total_requests"],
                    "successful_requests": metrics["successful_requests"],
                    "failed_requests": metrics["failed_requests"],
                    "error_rate": metrics["failed_requests"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0,
                    "inference_time": {
                        "avg": sum(inference_times) / len(inference_times),
                        "min": min(inference_times),
                        "max": max(inference_times),
                        "p95": sorted_times[p95_idx] if p95_idx < n else sorted_times[-1],
                        "p99": sorted_times[p99_idx] if p99_idx < n else sorted_times[-1]
                    },
                    "accuracy": {
                        "avg": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else None,
                        "min": min(accuracy_scores) if accuracy_scores else None,
                        "max": max(accuracy_scores) if accuracy_scores else None
                    }
                }
            else:
                result[model_name_key] = {
                    "model_name": model_name_key,
                    "total_requests": metrics["total_requests"],
                    "successful_requests": metrics["successful_requests"],
                    "failed_requests": metrics["failed_requests"],
                    "error_rate": metrics["failed_requests"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0,
                    "inference_time": None,
                    "accuracy": None
                }
        
        return result
    
    async def get_dashboard(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get dashboard data for all models.
        
        Returns:
            Dictionary with dashboard metrics
        """
        # Get metrics for all models
        all_metrics = await self.get_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate summary statistics
        total_requests = sum(m.get("total_requests", 0) for m in all_metrics.values())
        total_successful = sum(m.get("successful_requests", 0) for m in all_metrics.values())
        total_failed = sum(m.get("failed_requests", 0) for m in all_metrics.values())
        
        # Get average inference times
        avg_inference_times = {}
        for model_name, metrics in all_metrics.items():
            if metrics.get("inference_time"):
                avg_inference_times[model_name] = metrics["inference_time"]["avg"]
        
        # Get average accuracy
        avg_accuracy = {}
        for model_name, metrics in all_metrics.items():
            if metrics.get("accuracy") and metrics["accuracy"].get("avg"):
                avg_accuracy[model_name] = metrics["accuracy"]["avg"]
        
        return {
            "summary": {
                "total_requests": total_requests,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_error_rate": total_failed / total_requests if total_requests > 0 else 0
            },
            "models": all_metrics,
            "avg_inference_times": avg_inference_times,
            "avg_accuracy": avg_accuracy,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    
    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all models with their current status.
        """
        # Get unique model names from ModelVersion
        model_versions = self.db.query(ModelVersion).distinct().all()
        
        models = []
        for version in model_versions:
            model_name = version.model_name
            if not model_name:
                continue
            
            # Get latest log for this model
            latest_log = self.db.query(ModelInference).join(
                ModelVersion, ModelInference.model_id == ModelVersion.model_id
            ).filter(
                ModelVersion.model_name == model_name
            ).order_by(ModelInference.created_at.desc()).first()
            
            # Get recent metrics (last 24 hours)
            recent_metrics = await self.get_metrics(
                model_name=model_name,
                start_date=datetime.now() - timedelta(days=1)
            )
            
            model_metrics = recent_metrics.get(model_name, {})
            
            models.append({
                "model_name": model_name,
                "status": "available" if latest_log and hasattr(latest_log, 'success') and latest_log.success else "unavailable",
                "last_used": latest_log.created_at.isoformat() if latest_log else None,
                "recent_metrics": model_metrics
            })
        
        return models


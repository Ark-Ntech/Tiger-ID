"""
Model inference logging service.

Tracks model inference performance, errors, and usage statistics.
"""

import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import numpy as np

from backend.utils.logging import get_logger
from backend.config.settings import get_settings
from backend.database import get_db_session
from backend.database.models import ModelInference, ModelVersion

logger = get_logger(__name__)


class ModelInferenceLogger:
    """Service for logging model inference"""
    
    def __init__(self):
        """Initialize inference logger"""
        self.settings = get_settings()
        self.logger = logger
        
        # In-memory statistics
        self._stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_inferences': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'errors': []
        })
    
    def log_inference(
        self,
        model_name: str,
        success: bool,
        inference_time: float,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a model inference
        
        Args:
            model_name: Name of the model
            success: Whether inference was successful
            inference_time: Time taken for inference (seconds)
            error: Error message if failed
            metadata: Additional metadata
        """
        stats = self._stats[model_name]
        stats['total_inferences'] += 1
        
        if success:
            stats['successful'] += 1
        else:
            stats['failed'] += 1
            if error:
                stats['errors'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': error
                })
                # Keep only last 100 errors
                if len(stats['errors']) > 100:
                    stats['errors'] = stats['errors'][-100:]
        
        # Update timing statistics
        stats['total_time'] += inference_time
        stats['min_time'] = min(stats['min_time'], inference_time)
        stats['max_time'] = max(stats['max_time'], inference_time)
        
        # Log to database if configured
        if self.settings.database.enabled:
            try:
                self._log_to_database(
                    model_name, success, inference_time, error, metadata
                )
            except Exception as e:
                logger.warning(f"Failed to log inference to database: {e}")
        
        # Log to structured logger
        log_data = {
            'model': model_name,
            'success': success,
            'inference_time': inference_time,
            'error': error
        }
        if metadata:
            log_data.update(metadata)
        
        if success:
            logger.info("Model inference completed", **log_data)
        else:
            logger.error("Model inference failed", **log_data)
    
    def _log_to_database(
        self,
        model_name: str,
        success: bool,
        inference_time: float,
        error: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """
        Log inference to database
        
        Args:
            model_name: Name of the model
            success: Whether inference was successful
            inference_time: Time taken for inference
            error: Error message if failed
            metadata: Additional metadata
        """
        try:
            session = next(get_db_session())
            try:
                # Get or create model version
                model_version = session.query(ModelVersion).filter(
                    ModelVersion.model_name == model_name
                ).first()
                
                if not model_version:
                    model_version = ModelVersion(
                        model_name=model_name,
                        version="1.0.0",
                        is_active=True
                    )
                    session.add(model_version)
                    session.commit()
                    session.refresh(model_version)
                
                # Create inference log
                inference_log = ModelInference(
                    model_version_id=model_version.version_id,
                    success=success,
                    inference_time_ms=int(inference_time * 1000),
                    error_message=error,
                    metadata=metadata or {}
                )
                session.add(inference_log)
                session.commit()
            finally:
                session.close()
                
        except Exception as e:
            logger.warning(f"Error logging to database: {e}")
    
    def get_statistics(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get inference statistics
        
        Args:
            model_name: Name of model (None for all models)
            
        Returns:
            Dictionary with statistics
        """
        if model_name:
            stats = self._stats.get(model_name, {})
            if stats['total_inferences'] > 0:
                return {
                    'model': model_name,
                    'total_inferences': stats['total_inferences'],
                    'successful': stats['successful'],
                    'failed': stats['failed'],
                    'success_rate': stats['successful'] / stats['total_inferences'],
                    'avg_time': stats['total_time'] / stats['total_inferences'],
                    'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                    'max_time': stats['max_time'],
                    'recent_errors': stats['errors'][-10:]  # Last 10 errors
                }
            return {'model': model_name, 'no_data': True}
        else:
            # Return statistics for all models
            all_stats = {}
            for model, stats in self._stats.items():
                if stats['total_inferences'] > 0:
                    all_stats[model] = {
                        'total_inferences': stats['total_inferences'],
                        'successful': stats['successful'],
                        'failed': stats['failed'],
                        'success_rate': stats['successful'] / stats['total_inferences'],
                        'avg_time': stats['total_time'] / stats['total_inferences'],
                        'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                        'max_time': stats['max_time']
                    }
            return all_stats
    
    def reset_statistics(self, model_name: Optional[str] = None) -> None:
        """
        Reset inference statistics
        
        Args:
            model_name: Name of model (None for all models)
        """
        if model_name:
            if model_name in self._stats:
                self._stats[model_name] = {
                    'total_inferences': 0,
                    'successful': 0,
                    'failed': 0,
                    'total_time': 0.0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'errors': []
                }
                logger.info(f"Reset statistics for model: {model_name}")
        else:
            self._stats.clear()
            logger.info("Reset all inference statistics")


# Global inference logger instance
_inference_logger: Optional[ModelInferenceLogger] = None


def get_inference_logger() -> ModelInferenceLogger:
    """Get global inference logger instance"""
    global _inference_logger
    if _inference_logger is None:
        _inference_logger = ModelInferenceLogger()
    return _inference_logger


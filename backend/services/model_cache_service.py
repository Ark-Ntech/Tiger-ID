"""
Model caching and optimization service.

Implements model caching, batch processing optimization, and GPU memory management.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import torch
from functools import lru_cache
import asyncio
from collections import defaultdict

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class ModelCacheService:
    """Service for caching models and optimizing inference"""
    
    def __init__(self):
        """Initialize cache service"""
        self.settings = get_settings()
        self.logger = logger
        
        # Model cache
        self._model_cache: Dict[str, Any] = {}
        self._model_load_times: Dict[str, float] = {}
        
        # Embedding cache (for frequently queried images)
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._cache_max_size = 1000  # Maximum cached embeddings
        
        # Batch processing queue
        self._batch_queue: List[Dict[str, Any]] = []
        self._batch_size = 32
        self._batch_timeout = 0.1  # seconds
        
        # GPU memory management
        self._gpu_memory_limit = None
        if torch.cuda.is_available():
            # Set GPU memory limit (80% of available)
            total_memory = torch.cuda.get_device_properties(0).total_memory
            self._gpu_memory_limit = int(total_memory * 0.8)
            logger.info(f"GPU memory limit set to {self._gpu_memory_limit / (1024**3):.2f} GB")
    
    def get_cached_model(self, model_name: str) -> Optional[Any]:
        """
        Get cached model instance
        
        Args:
            model_name: Name of the model
            
        Returns:
            Cached model instance or None
        """
        return self._model_cache.get(model_name)
    
    def cache_model(self, model_name: str, model: Any) -> None:
        """
        Cache a model instance
        
        Args:
            model_name: Name of the model
            model: Model instance to cache
        """
        self._model_cache[model_name] = model
        self._model_load_times[model_name] = time.time()
        logger.debug(f"Cached model: {model_name}")
    
    def clear_model_cache(self, model_name: Optional[str] = None) -> None:
        """
        Clear model cache
        
        Args:
            model_name: Name of model to clear (None to clear all)
        """
        if model_name:
            if model_name in self._model_cache:
                del self._model_cache[model_name]
                del self._model_load_times[model_name]
                logger.info(f"Cleared cache for model: {model_name}")
        else:
            self._model_cache.clear()
            self._model_load_times.clear()
            logger.info("Cleared all model cache")
    
    def get_cached_embedding(self, image_hash: str) -> Optional[np.ndarray]:
        """
        Get cached embedding for an image
        
        Args:
            image_hash: Hash of the image
            
        Returns:
            Cached embedding or None
        """
        return self._embedding_cache.get(image_hash)
    
    def cache_embedding(self, image_hash: str, embedding: np.ndarray) -> None:
        """
        Cache an embedding
        
        Args:
            image_hash: Hash of the image
            embedding: Embedding vector to cache
        """
        # Evict oldest entries if cache is full
        if len(self._embedding_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._embedding_cache))
            del self._embedding_cache[oldest_key]
        
        self._embedding_cache[image_hash] = embedding
        logger.debug(f"Cached embedding for image: {image_hash[:8]}...")
    
    def clear_embedding_cache(self) -> None:
        """Clear embedding cache"""
        self._embedding_cache.clear()
        logger.info("Cleared embedding cache")
    
    async def batch_process_embeddings(
        self,
        model,
        images: List[Any],
        batch_size: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        Process images in batches for efficiency
        
        Args:
            model: Model instance
            images: List of images to process
            batch_size: Batch size (default: self._batch_size)
            
        Returns:
            List of embeddings
        """
        if batch_size is None:
            batch_size = self._batch_size
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            try:
                # Process batch
                batch_embeddings = await self._process_batch(model, batch)
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                # Add None embeddings for failed batch
                embeddings.extend([None] * len(batch))
        
        return embeddings
    
    async def _process_batch(self, model, batch: List[Any]) -> List[np.ndarray]:
        """
        Process a single batch of images
        
        Args:
            model: Model instance
            batch: List of images in batch
            
        Returns:
            List of embeddings
        """
        embeddings = []
        
        for image in batch:
            try:
                if hasattr(model, 'generate_embedding_from_bytes'):
                    # Assume image is bytes
                    embedding = await model.generate_embedding_from_bytes(image)
                elif hasattr(model, 'generate_embedding'):
                    # Assume image is PIL Image
                    embedding = await model.generate_embedding(image)
                else:
                    embedding = None
                
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"Error processing image in batch: {e}")
                embeddings.append(None)
        
        return embeddings
    
    def manage_gpu_memory(self) -> Dict[str, Any]:
        """
        Manage GPU memory usage
        
        Returns:
            Dictionary with memory statistics
        """
        if not torch.cuda.is_available():
            return {
                'available': False,
                'message': 'CUDA not available'
            }
        
        stats = {
            'available': True,
            'allocated_mb': torch.cuda.memory_allocated() / (1024 * 1024),
            'reserved_mb': torch.cuda.memory_reserved() / (1024 * 1024),
            'total_mb': torch.cuda.get_device_properties(0).total_memory / (1024 * 1024),
            'limit_mb': self._gpu_memory_limit / (1024 * 1024) if self._gpu_memory_limit else None
        }
        
        # Check if memory usage is high
        if self._gpu_memory_limit:
            usage_ratio = stats['reserved_mb'] / stats['limit_mb']
            stats['usage_ratio'] = usage_ratio
            
            if usage_ratio > 0.9:
                logger.warning(f"GPU memory usage high: {usage_ratio * 100:.1f}%")
                # Suggest clearing cache
                stats['recommendation'] = 'clear_cache'
            elif usage_ratio > 0.7:
                logger.info(f"GPU memory usage: {usage_ratio * 100:.1f}%")
                stats['recommendation'] = 'monitor'
            else:
                stats['recommendation'] = 'ok'
        
        return stats
    
    def clear_gpu_cache(self) -> None:
        """Clear GPU cache"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("Cleared GPU cache")
    
    def optimize_model_for_inference(self, model: Any) -> Any:
        """
        Optimize model for inference (quantization, etc.)
        
        Args:
            model: Model instance
            
        Returns:
            Optimized model
        """
        try:
            # Set model to eval mode
            if hasattr(model, 'eval'):
                model.eval()
            
            # Disable gradient computation
            if hasattr(model, 'requires_grad'):
                for param in model.parameters():
                    param.requires_grad = False
            
            # Try to use half precision if on GPU
            if torch.cuda.is_available() and hasattr(model, 'half'):
                try:
                    model = model.half()
                    logger.info("Model optimized to half precision")
                except Exception as e:
                    logger.warning(f"Could not convert to half precision: {e}")
            
            return model
            
        except Exception as e:
            logger.error(f"Error optimizing model: {e}")
            return model
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'models_cached': len(self._model_cache),
            'embeddings_cached': len(self._embedding_cache),
            'embedding_cache_max_size': self._cache_max_size,
            'model_load_times': self._model_load_times.copy(),
            'gpu_memory': self.manage_gpu_memory()
        }


# Global cache service instance
_cache_service: Optional[ModelCacheService] = None


def get_cache_service() -> ModelCacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = ModelCacheService()
    return _cache_service


"""ML model inference optimization"""

from typing import Optional, Dict, Any, List
import asyncio
from functools import lru_cache
import numpy as np

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ModelCache:
    """LRU cache for model inference results"""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize model cache
        
        Args:
            max_size: Maximum cache size
        """
        self.max_size = max_size
        self.cache = {}
    
    def get_cache_key(self, model_name: str, input_hash: str) -> str:
        """Generate cache key"""
        return f"{model_name}:{input_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any):
        """Set cached result"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = value
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()


class BatchProcessor:
    """Batch processor for model inference"""
    
    def __init__(self, batch_size: int = 8, max_wait: float = 0.1):
        """
        Initialize batch processor
        
        Args:
            batch_size: Maximum batch size
            max_wait: Maximum wait time before processing batch
        """
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.queue = []
        self.processing = False
    
    async def add_to_batch(self, item: Any) -> Any:
        """Add item to batch and return result"""
        self.queue.append(item)
        
        # Process if batch is full
        if len(self.queue) >= self.batch_size:
            return await self._process_batch()
        
        # Process after max wait
        await asyncio.sleep(self.max_wait)
        if len(self.queue) > 0:
            return await self._process_batch()
        
        return None
    
    async def _process_batch(self) -> List[Any]:
        """Process current batch"""
        if self.processing or len(self.queue) == 0:
            return []
        
        self.processing = True
        batch = self.queue[:self.batch_size]
        self.queue = self.queue[self.batch_size:]
        
        # Process batch (placeholder - actual processing depends on model)
        results = await self._process_items(batch)
        
        self.processing = False
        return results
    
    async def _process_items(self, items: List[Any]) -> List[Any]:
        """Process items in batch"""
        # Placeholder - actual implementation depends on model
        return items


def optimize_inference_batch(images: List[np.ndarray], batch_size: int = 8) -> List[np.ndarray]:
    """
    Optimize inference by batching images
    
    Args:
        images: List of images to process
        batch_size: Batch size
    
    Returns:
        List of processed images
    """
    batches = [images[i:i + batch_size] for i in range(0, len(images), batch_size)]
    
    results = []
    for batch in batches:
        # Process batch (placeholder)
        results.extend(batch)
    
    return results


def enable_model_caching(model_name: str, cache_size: int = 100):
    """
    Enable caching for a model
    
    Args:
        model_name: Name of the model
        cache_size: Cache size
    """
    cache = ModelCache(max_size=cache_size)
    logger.info(f"Caching enabled for model: {model_name} (size={cache_size})")
    return cache


# Global model caches
_model_caches: Dict[str, ModelCache] = {}


def get_model_cache(model_name: str) -> ModelCache:
    """Get or create model cache"""
    if model_name not in _model_caches:
        _model_caches[model_name] = ModelCache()
    return _model_caches[model_name]


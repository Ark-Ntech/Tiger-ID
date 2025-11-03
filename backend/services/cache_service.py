"""Redis caching service"""

from typing import Any, Optional, Union
import json
import pickle
from datetime import timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class CacheService:
    """Service for Redis caching"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        """
        Initialize cache service
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
        """
        self.default_ttl = default_ttl
        self.redis_client = None
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache service initialized")
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory cache: {e}")
                self.redis_client = None
                self._memory_cache = {}
        else:
            logger.warning("Redis library not available, using in-memory cache")
            self._memory_cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return pickle.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}", exc_info=True)
                return None
        else:
            # Use memory cache
            if key in self._memory_cache:
                data, expiry = self._memory_cache[key]
                if expiry and expiry < self._now():
                    del self._memory_cache[key]
                    return None
                return data
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        
        Returns:
            True if successful
        """
        ttl = ttl or self.default_ttl
        
        if self.redis_client:
            try:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}", exc_info=True)
                return False
        else:
            # Use memory cache
            expiry = self._now() + timedelta(seconds=ttl) if ttl > 0 else None
            self._memory_cache[key] = (value, expiry)
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if successful
        """
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}", exc_info=True)
                return False
        else:
            # Use memory cache
            if key in self._memory_cache:
                del self._memory_cache[key]
            return True
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        
        Args:
            pattern: Pattern to match (e.g., "investigation:*")
        
        Returns:
            Number of keys deleted
        """
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Redis clear pattern error: {e}", exc_info=True)
                return 0
        else:
            # Use memory cache
            import fnmatch
            deleted = 0
            for key in list(self._memory_cache.keys()):
                if fnmatch.fnmatch(key, pattern):
                    del self._memory_cache[key]
                    deleted += 1
            return deleted
    
    def get_or_set(
        self,
        key: str,
        callable_func: callable,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Get value from cache or compute and set if not exists
        
        Args:
            key: Cache key
            callable_func: Function to call if cache miss
            ttl: Time to live in seconds
            *args: Arguments for callable
            **kwargs: Keyword arguments for callable
        
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = callable_func(*args, **kwargs)
        self.set(key, value, ttl)
        return value
    
    def _now(self):
        """Get current datetime (for memory cache expiry)"""
        from datetime import datetime
        return datetime.utcnow()
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_client is not None


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service(redis_url: str = None, default_ttl: int = 3600) -> CacheService:
    """
    Get cache service instance (singleton)
    
    Args:
        redis_url: Redis connection URL (uses settings if None)
        default_ttl: Default TTL in seconds
    
    Returns:
        Cache service instance
    """
    global _cache_service
    
    if _cache_service is None:
        settings = get_settings()
        redis_url = redis_url or settings.redis.url
        _cache_service = CacheService(redis_url=redis_url, default_ttl=default_ttl)
    
    return _cache_service


"""Simple in-memory cache for analytics"""
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import hashlib
import json

_cache: Dict[str, Tuple[Any, datetime]] = {}
CACHE_TTL = timedelta(minutes=5)

def cached(ttl_minutes: int = 5):
    """Cache decorator for expensive functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hashlib.md5(json.dumps(str(args) + str(kwargs), sort_keys=True).encode()).hexdigest()}"
            
            # Check if cached and not expired
            if cache_key in _cache:
                result, timestamp = _cache[cache_key]
                if datetime.now() - timestamp < timedelta(minutes=ttl_minutes):
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, datetime.now())
            
            return result
        return wrapper
    return decorator

def clear_cache():
    """Clear all cached data"""
    global _cache
    _cache = {}

"""Enhanced error handling utilities"""

from typing import Dict, Any, Optional, List
import traceback
from functools import wraps
import asyncio

from backend.utils.error_types import ErrorInfo, ErrorCategory, create_error
from backend.utils.logging import get_logger
from backend.services.event_service import get_event_service
from backend.events.event_types import EventType

logger = get_logger(__name__)


def handle_error(
    error: Exception,
    category: ErrorCategory = ErrorCategory.RECOVERABLE,
    investigation_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> ErrorInfo:
    """
    Handle an error and create structured error info
    
    Args:
        error: Exception that occurred
        category: Error category
        investigation_id: Optional investigation ID
        agent_name: Optional agent name
        context: Optional context
    
    Returns:
        ErrorInfo object
    """
    error_info = create_error(
        category=category,
        message=str(error),
        details={
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "agent": agent_name,
            "context": context or {}
        },
        recovery_options=_get_recovery_options(category, error)
    )
    
    # Log error
    logger.error(
        f"Error occurred: {error_info.message}",
        error_id=error_info.error_id,
        category=category.value,
        agent=agent_name,
        investigation_id=investigation_id,
        exc_info=True
    )
    
    # Emit error event (only if there's a running event loop)
    event_service = get_event_service()
    if event_service:
        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
            asyncio.create_task(event_service.emit(
                EventType.ERROR_OCCURRED.value,
                {
                    "error_id": error_info.error_id,
                    "category": category.value,
                    "message": error_info.message,
                    "agent": agent_name,
                    "can_retry": error_info.can_retry,
                    "recovery_options": error_info.recovery_options
                },
                investigation_id=investigation_id
            ))
        except RuntimeError:
            # No event loop running (sync context), skip event emission
            logger.debug("No event loop available, skipping event emission")
    
    return error_info


def _get_recovery_options(category: ErrorCategory, error: Exception) -> List[str]:
    """Get recovery options based on error category"""
    options = []
    
    if category == ErrorCategory.RETRYABLE:
        options.append("retry")
        options.append("retry_with_backoff")
    
    if category == ErrorCategory.RECOVERABLE:
        options.append("continue")
        options.append("skip_step")
        options.append("fallback")
    
    if category == ErrorCategory.NETWORK:
        options.append("retry")
        options.append("use_cached_data")
    
    if category == ErrorCategory.EXTERNAL_API:
        options.append("retry")
        options.append("use_alternative_provider")
        options.append("skip_external_api")
    
    if category == ErrorCategory.AGENT:
        options.append("retry")
        options.append("skip_agent")
        options.append("use_fallback_agent")
    
    if category == ErrorCategory.VALIDATION:
        options.append("correct_input")
        options.append("use_defaults")
    
    return options


def retry_on_error(
    max_retries: int = 3,
    backoff: float = 1.0,
    retryable_categories: Optional[List[ErrorCategory]] = None
):
    """
    Decorator to retry function on error
    
    Args:
        max_retries: Maximum retry attempts
        backoff: Backoff multiplier
        retryable_categories: Categories to retry on
    """
    if retryable_categories is None:
        retryable_categories = [ErrorCategory.RETRYABLE, ErrorCategory.RECOVERABLE, ErrorCategory.NETWORK]
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Determine error category
                    error_info = handle_error(e, context={"attempt": attempt + 1})
                    
                    if error_info.category not in retryable_categories:
                        raise
                    
                    if attempt < max_retries:
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(
                            f"Retrying {func.__name__} after {wait_time}s (attempt {attempt + 1}/{max_retries})",
                            error=str(e)
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"Failed after {max_retries} retries: {func.__name__}",
                            error=str(last_error)
                        )
                        raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    error_info = handle_error(e, context={"attempt": attempt + 1})
                    
                    if error_info.category not in retryable_categories:
                        raise
                    
                    if attempt < max_retries:
                        import time
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(
                            f"Retrying {func.__name__} after {wait_time}s (attempt {attempt + 1}/{max_retries})",
                            error=str(e)
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Failed after {max_retries} retries: {func.__name__}",
                            error=str(last_error)
                        )
                        raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def fallback_on_error(fallback_func=None, fallback_value=None):
    """
    Decorator to use fallback on error
    
    Args:
        fallback_func: Fallback function to call
        fallback_value: Fallback value to return
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_info = handle_error(e, category=ErrorCategory.RECOVERABLE)
                
                if fallback_func:
                    logger.info(f"Using fallback function for {func.__name__}")
                    return await fallback_func(*args, **kwargs)
                elif fallback_value is not None:
                    logger.info(f"Using fallback value for {func.__name__}")
                    return fallback_value
                else:
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = handle_error(e, category=ErrorCategory.RECOVERABLE)
                
                if fallback_func:
                    logger.info(f"Using fallback function for {func.__name__}")
                    return fallback_func(*args, **kwargs)
                elif fallback_value is not None:
                    logger.info(f"Using fallback value for {func.__name__}")
                    return fallback_value
                else:
                    raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


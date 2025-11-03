"""Sentry error tracking configuration"""

from typing import Optional

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


def initialize_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
) -> bool:
    """
    Initialize Sentry error tracking
    
    Args:
        dsn: Sentry DSN (uses settings if None)
        environment: Environment name (uses settings if None)
        traces_sample_rate: Sample rate for performance traces (uses settings if None)
        profiles_sample_rate: Sample rate for profiling (uses settings if None)
    
    Returns:
        True if Sentry was initialized, False otherwise
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not available - error tracking disabled")
        return False
    
    settings = get_settings()
    dsn = dsn or settings.sentry.dsn
    environment = environment or settings.sentry.environment
    traces_sample_rate = traces_sample_rate if traces_sample_rate is not None else settings.sentry.traces_sample_rate
    profiles_sample_rate = profiles_sample_rate if profiles_sample_rate is not None else settings.sentry.profiles_sample_rate
    
    if not dsn:
        logger.warning("SENTRY_DSN not configured - error tracking disabled")
        return False
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            # Set user context
            before_send=lambda event, hint: event,  # Can add custom filtering
        )
        
        logger.info(f"Sentry initialized for environment: {environment}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)
        return False


def capture_exception(error: Exception, context: Optional[dict] = None):
    """
    Capture exception in Sentry
    
    Args:
        error: Exception to capture
        context: Additional context data
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        try:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                sentry_sdk.capture_exception(error)
        except Exception as e:
            logger.error(f"Failed to capture exception in Sentry: {e}", exc_info=True)


def capture_message(message: str, level: str = "info", context: Optional[dict] = None):
    """
    Capture message in Sentry
    
    Args:
        message: Message to capture
        level: Log level (info, warning, error)
        context: Additional context data
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        try:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                sentry_sdk.capture_message(message, level=level)
        except Exception as e:
            logger.error(f"Failed to capture message in Sentry: {e}", exc_info=True)


def set_user_context(user_id: str, username: str = None, email: str = None):
    """
    Set user context for Sentry
    
    Args:
        user_id: User ID
        username: Username
        email: User email
    """
    if SENTRY_AVAILABLE and sentry_sdk:
        sentry_sdk.set_user({
            "id": user_id,
            "username": username,
            "email": email
        })


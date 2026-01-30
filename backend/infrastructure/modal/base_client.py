"""Base Modal client with retry logic and connection management."""

import asyncio
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ModalClientError(Exception):
    """Base exception for Modal client errors."""
    pass


class ModalUnavailableError(ModalClientError):
    """Raised when Modal service is unavailable."""
    pass


class BaseModalClient(ABC):
    """Base class for Modal clients with common retry and connection logic.

    Provides:
    - Retry logic with exponential backoff
    - Request timeout handling
    - Statistics tracking
    - Lazy function loading
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 120,
        use_mock: Optional[bool] = None
    ):
        """Initialize base Modal client.

        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
            timeout: Request timeout in seconds
            use_mock: Use mock responses instead of real Modal
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # Check if mock mode enabled via environment variable
        import os
        self.use_mock = (
            use_mock if use_mock is not None
            else os.getenv("MODAL_USE_MOCK", "false").lower() == "true"
        )

        if self.use_mock:
            logger.warning(f"[{self.__class__.__name__}] MOCK MODE ENABLED")
        else:
            logger.info(f"[{self.__class__.__name__}] Production mode")

        # Stats
        self.stats = {
            "requests_sent": 0,
            "requests_succeeded": 0,
            "requests_failed": 0,
        }

        # Cached Modal function
        self._modal_function = None

    @property
    @abstractmethod
    def app_name(self) -> str:
        """Get the Modal app name."""
        pass

    @property
    @abstractmethod
    def class_name(self) -> str:
        """Get the Modal class name."""
        pass

    def _get_modal_function(self):
        """Lazy load Modal function reference.

        Returns:
            Modal function reference
        """
        if self._modal_function is not None:
            return self._modal_function

        logger.info(
            f"[{self.__class__.__name__}] Connecting to Modal app "
            f"'{self.app_name}' class '{self.class_name}'..."
        )

        try:
            import modal

            model_cls = modal.Cls.from_name(self.app_name, self.class_name)
            self._modal_function = model_cls()

            logger.info(f"[{self.__class__.__name__}] Modal instance created")
            return self._modal_function

        except Exception as e:
            logger.error(
                f"[{self.__class__.__name__}] Failed to connect: {e}",
                exc_info=True
            )
            raise ModalUnavailableError(f"Failed to connect to Modal: {e}")

    async def _call_with_retry(
        self,
        method_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Call Modal function method with retry logic.

        Args:
            method_name: Name of the method to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Method result

        Raises:
            ModalClientError: If all retries fail
        """
        last_error = None

        logger.info(
            f"[{self.__class__.__name__}] Calling {method_name} "
            f"(max_retries={self.max_retries})"
        )

        for attempt in range(self.max_retries):
            try:
                self.stats["requests_sent"] += 1

                model = self._get_modal_function()
                method = getattr(model, method_name)

                result = await asyncio.wait_for(
                    method.remote.aio(*args, **kwargs),
                    timeout=self.timeout
                )

                self.stats["requests_succeeded"] += 1
                logger.info(
                    f"[{self.__class__.__name__}] {method_name} succeeded "
                    f"on attempt {attempt + 1}"
                )
                return result

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    f"[{self.__class__.__name__}] Timeout on attempt "
                    f"{attempt + 1}/{self.max_retries}"
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.__class__.__name__}] Failed on attempt "
                    f"{attempt + 1}/{self.max_retries}: {type(e).__name__}: {e}"
                )

            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)

        # All retries failed
        self.stats["requests_failed"] += 1
        raise ModalClientError(
            f"Request failed after {self.max_retries} attempts: {last_error}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics.

        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            "requests_sent": 0,
            "requests_succeeded": 0,
            "requests_failed": 0,
        }

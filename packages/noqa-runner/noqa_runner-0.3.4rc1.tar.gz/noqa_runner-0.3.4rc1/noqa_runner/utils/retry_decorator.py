"""Universal retry decorator with logging"""

from __future__ import annotations

from typing import Type

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from noqa_runner.logging_config import get_logger

logger = get_logger(__name__)


def log_retry_attempt(retry_state: RetryCallState):
    """Log each retry attempt with full exception traceback"""
    if retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        logger.warning(
            "retry_attempt",
            attempt=retry_state.attempt_number,
            function=retry_state.fn.__name__,
            error=str(exception),
            error_type=type(exception).__name__,
        )


def with_retry(
    max_attempts: int = 10,
    min_wait: int = 1,
    max_wait: int = 3,
    exclude_exceptions: tuple[Type[Exception], ...] = (),
    exceptions: tuple[Type[Exception], ...] | None = None,
):
    """Universal retry decorator with exponential backoff and logging

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds between retries
        max_wait: Maximum wait time in seconds between retries
        exceptions: Tuple of exception types to retry on. Defaults to (Exception,) - all exceptions.
        exclude_exceptions: Tuple of exception types to NOT retry on (even if in exceptions).

    Example:
        @with_retry(max_attempts=3, exceptions=(httpx.HTTPError,))
        async def fetch_data():
            ...
    """

    def decorator(func):
        def should_retry(exception: Exception) -> bool:
            # Don't retry if exception is in exclude_exceptions
            if isinstance(exception, exclude_exceptions):
                return False

            # Don't retry client errors (4xx) for HTTPStatusError; defer 429 (rate limit) to the exceptions tuple
            if isinstance(exception, httpx.HTTPStatusError):
                status_code = exception.response.status_code
                if 400 <= status_code < 500 and status_code != 429:
                    return False

            if exceptions:
                # Retry only if exception matches allowed exceptions
                return isinstance(exception, exceptions)

            # If no exceptions specified, retry all exceptions (except excluded above)
            return True

        retry_condition = retry_if_exception(should_retry)

        return retry(
            retry=retry_condition,
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            before_sleep=log_retry_attempt,
            reraise=True,  # Re-raise the original exception instead of MaxRetryError
        )(func)

    return decorator

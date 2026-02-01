"""
Gate SDK - Retry Logic

Exponential backoff with jitter for retryable requests.
"""

import logging
import time
import random
from typing import Callable, TypeVar, Optional

from .errors import GateError, GateRateLimitError, GateServerError

T = TypeVar("T")
LOG = logging.getLogger("gate_sdk.retry")


def is_retryable_status(status: int) -> bool:
    """
    Determine if an HTTP status code is retryable.

    Args:
        status: HTTP status code

    Returns:
        True if status is retryable (429 or 5xx)
    """
    return status == 429 or (500 <= status < 600)


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.

    Args:
        error: Exception to check

    Returns:
        True if error is retryable
    """
    if isinstance(error, GateError):
        return isinstance(error, (GateRateLimitError, GateServerError))
    return False


def calculate_backoff_delay(
    attempt: int,
    base_delay_ms: int = 100,
    max_delay_ms: int = 800,
    factor: float = 2.0,
) -> float:
    """
    Calculate delay with exponential backoff and jitter.

    Args:
        attempt: Current attempt number (1-based)
        base_delay_ms: Base delay in milliseconds
        max_delay_ms: Maximum delay in milliseconds
        factor: Exponential factor

    Returns:
        Delay in seconds
    """
    exponential_delay = base_delay_ms * (factor ** (attempt - 1))
    jitter = random.random() * 0.3 * exponential_delay  # 0-30% jitter
    delay = exponential_delay + jitter
    return min(delay, max_delay_ms) / 1000.0  # Convert to seconds


def retry_with_backoff(
    fn: Callable[[], T],
    max_attempts: int = 3,
    base_delay_ms: int = 100,
    max_delay_ms: int = 800,
    factor: float = 2.0,
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        fn: Function to retry (should raise exception on failure)
        max_attempts: Maximum number of attempts
        base_delay_ms: Base delay in milliseconds
        max_delay_ms: Maximum delay in milliseconds
        factor: Exponential factor

    Returns:
        Result of function call

    Raises:
        Last exception if all attempts fail
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as error:
            last_error = error

            # Don't retry if we've exhausted attempts
            if attempt >= max_attempts:
                break

            # Don't retry on non-retryable errors
            if isinstance(error, GateError):
                if not is_retryable_error(error):
                    raise
            else:
                # For non-GateError exceptions, check if they're retryable
                if not is_retryable_error(error):
                    raise

            # Log degraded once per attempt (logs/telemetry only; never sent as HTTP request header)
            status = getattr(error, "status_code", None) or getattr(error, "status", None)
            req_id = getattr(error, "request_id", None) or getattr(error, "correlation_id", None)
            extra = f" attempt={attempt}/{max_attempts} status={status} exc={type(error).__name__}"
            if req_id:
                extra += f" requestId={req_id}"
            LOG.warning("[GATE SDK] X-BlockIntel-Degraded: true (reason=retry)%s", extra)

            # Wait before retrying
            delay = calculate_backoff_delay(attempt, base_delay_ms, max_delay_ms, factor)
            time.sleep(delay)

    # If we get here, all attempts failed
    if last_error:
        raise last_error
    raise Exception("All retry attempts failed")


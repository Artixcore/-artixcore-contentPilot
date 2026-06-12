"""Retry utilities with exponential backoff and jitter."""

from __future__ import annotations

import functools
import random
import time
from collections.abc import Callable
from typing import Any, TypeVar

from core.error_handler import is_retryable_error
from core.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def is_transient_exception(exc: BaseException) -> bool:
    """Return True if exception is likely transient."""
    return is_retryable_error(exc)


def retry_with_backoff(
    fn: Callable[..., T],
    *args,
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retryable_exceptions: tuple[type[BaseException], ...] | None = None,
    on_retry: Callable[[int, BaseException], None] | None = None,
    **kwargs,
) -> T:
    """Execute fn with retries on transient failures."""
    last_exc: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if retryable_exceptions and not isinstance(exc, retryable_exceptions):
                raise
            if not is_retryable_error(exc):
                raise
            if attempt >= retries:
                raise
            delay = min(max_delay, base_delay * (2 ** attempt))
            delay += random.uniform(0, delay * 0.25)
            if on_retry:
                on_retry(attempt + 1, exc)
            else:
                logger.warning(
                    "Retry %s/%s after %s: %s",
                    attempt + 1,
                    retries,
                    type(exc).__name__,
                    delay,
                )
            time.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_with_backoff failed without exception")


def retry_on_sqlite_locked(max_retries: int = 3, base_delay: float = 0.5):
    """Decorator to retry database operations on SQLite locked errors."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            def _is_locked(exc: BaseException) -> bool:
                msg = str(exc).lower()
                return "locked" in msg or "database is locked" in msg

            last_exc: BaseException | None = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if not _is_locked(exc):
                        raise
                    last_exc = exc
                    if attempt >= max_retries:
                        raise
                    delay = min(5.0, base_delay * (2 ** attempt)) + random.uniform(0, 0.1)
                    logger.warning("SQLite locked, retry %s/%s", attempt + 1, max_retries)
                    time.sleep(delay)
            if last_exc:
                raise last_exc
            raise RuntimeError("retry_on_sqlite_locked failed")

        return wrapper

    return decorator

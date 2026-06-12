"""Concurrency and load management for heavy operations."""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Generator

from core.errors import LoadLimitError, TimeoutAppError
from core.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_API_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_API_TIMEOUT_SECONDS", "30"))
LONG_TASK_TIMEOUT_SECONDS = int(os.getenv("LONG_TASK_TIMEOUT_SECONDS", "120"))

_LIMITS: dict[str, int] = {
    "ai": int(os.getenv("MAX_CONCURRENT_AI_REQUESTS", "3")),
    "publish": int(os.getenv("MAX_CONCURRENT_PUBLISH_REQUESTS", "2")),
    "export": int(os.getenv("MAX_CONCURRENT_EXPORTS", "2")),
}

_SEMAPHORES: dict[str, threading.Semaphore] = {}
_LOCK = threading.Lock()


def _get_semaphore(operation_type: str) -> threading.Semaphore:
    with _LOCK:
        if operation_type not in _SEMAPHORES:
            limit = _LIMITS.get(operation_type, 2)
            _SEMAPHORES[operation_type] = threading.Semaphore(limit)
        return _SEMAPHORES[operation_type]


def acquire_slot(operation_type: str, timeout: float | None = None) -> bool:
    """Try to acquire a concurrency slot. Returns False if unavailable."""
    timeout = timeout if timeout is not None else float(DEFAULT_API_TIMEOUT_SECONDS)
    sem = _get_semaphore(operation_type)
    acquired = sem.acquire(timeout=timeout)
    if not acquired:
        logger.warning("Load limit reached for operation=%s", operation_type)
    return acquired


def release_slot(operation_type: str) -> None:
    sem = _get_semaphore(operation_type)
    try:
        sem.release()
    except ValueError:
        pass


@contextmanager
def with_load_slot(operation_type: str, timeout: float | None = None) -> Generator[None, None, None]:
    """Context manager for load-limited operations."""
    if not acquire_slot(operation_type, timeout=timeout):
        raise LoadLimitError()
    try:
        yield
    finally:
        release_slot(operation_type)


def reset_load_manager() -> None:
    """Reset semaphores (for tests)."""
    with _LOCK:
        _SEMAPHORES.clear()


def get_load_status() -> dict:
    status = {}
    for op_type, limit in _LIMITS.items():
        sem = _get_semaphore(op_type)
        available = getattr(sem, "_value", limit)
        status[op_type] = {"limit": limit, "available_slots": available}
    return status


def enforce_timeout(seconds: int | None, message: str = "Operation timed out.") -> None:
    """Placeholder for timeout enforcement at call sites."""
    if seconds is not None and seconds <= 0:
        raise TimeoutAppError(message)

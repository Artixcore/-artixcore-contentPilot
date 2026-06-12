"""In-memory circuit breaker for external API calls."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from core.errors import ExternalAPIError
from core.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
COOLDOWN_SECONDS = int(os.getenv("CIRCUIT_BREAKER_COOLDOWN_SECONDS", "60"))

_REGISTRY: dict[str, "CircuitBreaker"] = {}
_LOCK = threading.Lock()


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker with closed/open/half-open states."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = FAILURE_THRESHOLD,
        cooldown_seconds: int = COOLDOWN_SECONDS,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_half_open()
            return self._state

    def _maybe_transition_half_open(self) -> None:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker %s entering half-open", self.name)

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "Circuit breaker %s opened after %s failures",
                    self.name,
                    self._failure_count,
                )

    def allow_request(self) -> bool:
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True
        return False

    def call(self, fn: Callable[..., T], *args, **kwargs) -> T:
        if not self.allow_request():
            raise ExternalAPIError(
                "This connector is temporarily paused after repeated failures. "
                "Please wait or check configuration.",
                service=self.name,
                error_code="CIRCUIT_OPEN",
            )
        try:
            result = fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise


def get_breaker(name: str) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    with _LOCK:
        if name not in _REGISTRY:
            _REGISTRY[name] = CircuitBreaker(name)
        return _REGISTRY[name]


def circuit_call(name: str, fn: Callable[..., T], *args, **kwargs) -> T:
    """Execute fn through the named circuit breaker."""
    return get_breaker(name).call(fn, *args, **kwargs)


def reset_breakers() -> None:
    """Reset all circuit breakers (for tests)."""
    with _LOCK:
        _REGISTRY.clear()


def get_breaker_status(name: str) -> dict[str, Any]:
    breaker = get_breaker(name)
    return {
        "name": name,
        "state": breaker.state.value,
        "failure_count": breaker._failure_count,
    }

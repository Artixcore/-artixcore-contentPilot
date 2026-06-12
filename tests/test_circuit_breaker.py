"""Tests for core.circuit_breaker."""

import pytest

from core.circuit_breaker import CircuitBreaker, reset_breakers
from core.errors import ExternalAPIError


@pytest.fixture(autouse=True)
def clean_breakers():
    reset_breakers()
    yield
    reset_breakers()


def test_opens_after_repeated_failures():
    breaker = CircuitBreaker("test_svc", failure_threshold=3, cooldown_seconds=60)

    def fail():
        raise RuntimeError("down")

    for _ in range(3):
        with pytest.raises(RuntimeError):
            breaker.call(fail)
    assert breaker.state.value == "open"


def test_blocks_calls_while_open():
    breaker = CircuitBreaker("test_svc2", failure_threshold=1, cooldown_seconds=60)

    with pytest.raises(RuntimeError):
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))

    with pytest.raises(ExternalAPIError):
        breaker.call(lambda: "ok")


def test_half_open_after_cooldown(monkeypatch):
    breaker = CircuitBreaker("test_svc3", failure_threshold=1, cooldown_seconds=0)

    with pytest.raises(RuntimeError):
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))

    monkeypatch.setattr("core.circuit_breaker.time.monotonic", lambda: 1000.0)
    breaker._opened_at = 0.0
    assert breaker.state.value == "half_open"

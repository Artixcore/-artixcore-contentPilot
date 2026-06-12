"""Tests for core.rate_limiter."""

import pytest

from core.errors import RateLimitError
from core.rate_limiter import check_rate_limit, reset_rate_limits


@pytest.fixture(autouse=True)
def clean_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


def test_allows_within_limit(monkeypatch):
    monkeypatch.setenv("AI_RATE_LIMIT_PER_MINUTE", "5")
    import importlib
    import core.rate_limiter as rl

    importlib.reload(rl)
    for _ in range(5):
        remaining = rl.check_rate_limit("ai_generation", key="test")
        assert remaining >= 0


def test_blocks_over_limit(monkeypatch):
    monkeypatch.setenv("AI_RATE_LIMIT_PER_MINUTE", "2")
    import importlib
    import core.rate_limiter as rl

    importlib.reload(rl)
    rl.reset_rate_limits()
    rl.check_rate_limit("ai_generation", key="block")
    rl.check_rate_limit("ai_generation", key="block")
    with pytest.raises(RateLimitError):
        rl.check_rate_limit("ai_generation", key="block")

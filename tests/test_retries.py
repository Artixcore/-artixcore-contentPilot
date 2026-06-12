"""Tests for core.retries."""

import pytest

from core.errors import ValidationAppError
from core.retries import retry_with_backoff


def test_retries_retryable_error():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("network down")
        return "ok"

    result = retry_with_backoff(flaky, retries=3, base_delay=0.01, max_delay=0.05)
    assert result == "ok"
    assert calls["n"] == 3


def test_does_not_retry_validation_error():
    def bad():
        raise ValidationAppError("invalid")

    with pytest.raises(ValidationAppError):
        retry_with_backoff(bad, retries=3, base_delay=0.01)


def test_backoff_works():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise TimeoutError("timeout")
        return True

    assert retry_with_backoff(flaky, retries=2, base_delay=0.01) is True

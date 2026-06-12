"""Tests for core.safe_runner."""

from core.safe_runner import safe_execute


def test_catches_exception():
    def boom():
        raise ValueError("fail")

    result = safe_execute(boom, context="test")
    assert result["success"] is False
    assert result["error"] is not None


def test_returns_fallback():
    def boom():
        raise ValueError("fail")

    result = safe_execute(boom, fallback="default", context="test")
    assert result["result"] == "default"


def test_success_path():
    result = safe_execute(lambda x: x + 1, 1, context="test")
    assert result["success"] is True
    assert result["result"] == 2


def test_does_not_crash():
    result = safe_execute(lambda: 1 / 0, context="test")
    assert result["success"] is False

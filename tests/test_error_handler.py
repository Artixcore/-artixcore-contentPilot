"""Tests for core.error_handler."""

import os

import pytest

from core.error_handler import (
    format_user_error,
    handle_exception,
    is_retryable_error,
    safe_error_message,
)
from core.errors import AppError, RateLimitError, ValidationAppError
from core.utils import sanitize_text


def test_formats_app_error():
    err = AppError("Something failed", reason="Test reason", error_code="TEST")
    result = format_user_error(err)
    assert result["success"] is False
    assert result["message"] == "Something failed"
    assert result["reason"] == "Test reason"
    assert result["error_code"] == "TEST"


def test_sanitizes_secrets():
    raw = "Bearer sk-1234567890abcdef and Authorization: Bearer secret-token"
    cleaned = sanitize_text(raw)
    assert "sk-1234567890abcdef" not in cleaned
    assert "secret-token" not in cleaned


def test_hides_traceback_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_DEBUG", "false")
    import importlib
    import core.error_handler as eh

    importlib.reload(eh)
    result = eh.format_user_error(ValueError("boom"))
    assert "traceback" not in result


def test_shows_traceback_in_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_DEBUG", "false")
    import importlib
    import core.error_handler as eh

    importlib.reload(eh)
    result = eh.format_user_error(ValueError("boom"))
    assert "traceback" in result


def test_marks_retryable_errors():
    assert is_retryable_error(RateLimitError()) is True
    assert is_retryable_error(ValidationAppError("bad input")) is False


def test_handle_exception_structure():
    result = handle_exception(ValidationAppError("Invalid"), context="test")
    assert result["success"] is False
    assert result["retryable"] is False
    assert "message" in result


def test_safe_error_message():
    msg = safe_error_message(AppError("User message"))
    assert msg == "User message"

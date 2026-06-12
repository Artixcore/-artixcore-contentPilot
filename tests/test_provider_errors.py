"""Tests for AI provider error handling."""

import pytest

from core.errors import AuthenticationConfigError
from providers.anthropic_provider import AnthropicProvider
from providers.base import ProviderError
from providers.openai_provider import OpenAIProvider


def test_openai_missing_key_clean_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIProvider()
    with pytest.raises(AuthenticationConfigError):
        provider.generate("hello")


def test_anthropic_missing_key_clean_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicProvider()
    with pytest.raises(AuthenticationConfigError):
        provider.generate("hello")


def test_openai_not_available():
    provider = OpenAIProvider()
    provider.api_key = ""
    assert provider.is_available() is False


def test_friendly_timeout_mapping():
    from providers.openai_provider import _map_openai_error

    err = _map_openai_error(TimeoutError("request timeout"))
    assert "timed out" in err.message.lower()


def test_invalid_response_mapping():
    from providers.openai_provider import _map_openai_error

    err = _map_openai_error(Exception("model not found 404"))
    assert "model" in err.message.lower()

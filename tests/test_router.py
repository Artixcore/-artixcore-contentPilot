"""Tests for provider router."""

import pytest

from core.router import ProviderRouter
from providers import get_all_providers
from providers.base import ProviderUnavailableError


def test_no_mock_provider_in_registry():
    providers = get_all_providers()
    assert "mock" not in providers
    assert set(providers.keys()) == {"openai", "anthropic"}


def test_auto_mode_raises_when_no_keys(db_session):
    router = ProviderRouter(session=db_session)
    with pytest.raises(ProviderUnavailableError):
        router.resolve_provider(mode="auto")


def test_quality_mode_raises_when_no_keys(db_session):
    router = ProviderRouter(session=db_session)
    with pytest.raises(ProviderUnavailableError):
        router.resolve_provider(mode="quality")


def test_manual_mode_raises_when_unavailable(db_session):
    router = ProviderRouter(session=db_session)
    with pytest.raises(ProviderUnavailableError):
        router.resolve_provider(mode="manual", selected_provider="openai")


def test_fallback_mode_raises_when_no_keys(db_session):
    router = ProviderRouter(session=db_session)
    with pytest.raises(ProviderUnavailableError):
        router.resolve_provider(mode="fallback", selected_provider="anthropic")


def test_generate_raises_when_no_keys(db_session):
    router = ProviderRouter(session=db_session)
    with pytest.raises(ProviderUnavailableError):
        router.generate(prompt="test", system_prompt="system", mode="auto")


def test_auto_mode_prefers_openai_when_key_present(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-openai")
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="auto")
    assert provider.name == "openai"


def test_quality_mode_prefers_anthropic_when_key_present(db_session, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-anthropic")
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="quality")
    assert provider.name == "anthropic"


def test_fallback_from_unavailable_to_available(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-openai")
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="fallback", selected_provider="anthropic")
    assert provider.name == "openai"


def test_openai_available_when_key_exists(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    router = ProviderRouter(session=db_session)
    assert router.is_provider_available("openai") is True
    assert router.is_provider_available("anthropic") is False


def test_anthropic_available_when_key_exists(db_session, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    router = ProviderRouter(session=db_session)
    assert router.is_provider_available("anthropic") is True
    assert router.is_provider_available("openai") is False

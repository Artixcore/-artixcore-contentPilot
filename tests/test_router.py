"""Tests for provider router."""

import pytest

from core.router import ProviderRouter


def test_auto_mode_uses_mock_when_no_keys(db_session):
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="auto")
    assert provider.name == "mock"


def test_budget_mode_uses_mock(db_session):
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="budget")
    assert provider.name == "mock"


def test_quality_mode_uses_mock_when_no_keys(db_session):
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="quality")
    assert provider.name == "mock"


def test_manual_mode_fallback_to_mock(db_session):
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="manual", selected_provider="openai")
    assert provider.name == "mock"


def test_fallback_mode_when_selected_unavailable(db_session):
    router = ProviderRouter(session=db_session)
    provider = router.resolve_provider(mode="fallback", selected_provider="anthropic")
    assert provider.name == "mock"


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


def test_generate_with_mock_provider(db_session):
    router = ProviderRouter(session=db_session)
    result = router.generate(
        prompt="Generate a test post",
        system_prompt="You are a test assistant.",
        mode="auto",
        platform="facebook",
        topic="SaaS development",
    )
    assert result.success
    assert result.provider == "mock"
    assert result.text

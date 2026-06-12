"""Tests for ContentPilot agent."""

from unittest.mock import patch

import pytest

from core.agent import AgentValidationError, ContentPilotAgent
from core.models import Post
from providers import PROVIDER_UNAVAILABLE_MSG
from providers.base import GenerationResult


def test_generation_blocked_when_no_provider(db_session):
    agent = ContentPilotAgent(db_session)
    with pytest.raises(AgentValidationError, match="OpenAI or Anthropic"):
        agent.generate_post(
            platform="facebook",
            topic="SaaS MVP development",
            goal="Drive consultations",
            tone="Professional",
            language="English",
            cta="Book a consultation",
        )


def test_invalid_platform_raises(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    agent = ContentPilotAgent(db_session)
    with pytest.raises(AgentValidationError, match="Unsupported platform"):
        agent.generate_post(
            platform="tiktok",
            topic="Test topic",
            goal="",
            tone="",
            language="English",
            cta="",
        )


def test_empty_topic_raises(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    agent = ContentPilotAgent(db_session)
    with pytest.raises(AgentValidationError, match="Topic is required"):
        agent.generate_post(
            platform="linkedin",
            topic="  ",
            goal="",
            tone="",
            language="English",
            cta="",
        )


def test_invalid_json_handled_safely(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    agent = ContentPilotAgent(db_session)

    mock_result = GenerationResult(
        text="This is raw non-json content from the model.",
        provider="openai",
        model="gpt-4.1-mini",
        latency_ms=100,
    )

    with patch.object(agent.router, "generate", return_value=mock_result):
        with patch.object(agent.router, "has_any_provider", return_value=True):
            result = agent.generate_post(
                platform="linkedin",
                topic="AI automation",
                goal="Awareness",
                tone="Professional",
                language="English",
                cta="Visit Artixcore",
            )

    assert result.saved
    assert result.content == mock_result.text
    assert result.post_id is not None

    post = db_session.get(Post, result.post_id)
    assert post.status == "pending_approval"
    assert "invalid JSON" in (post.quality_notes or "").lower() or post.raw_ai_response


def test_successful_generation_saves_training_fields(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    agent = ContentPilotAgent(db_session)

    json_response = (
        '{"content": "Great post about SaaS.", "hashtags": ["SaaS"], '
        '"image_prompt": "", "quality_notes": "Good"}'
    )
    mock_result = GenerationResult(
        text=json_response,
        provider="openai",
        model="gpt-4.1-mini",
        latency_ms=200,
        token_input_estimate=50,
        token_output_estimate=100,
    )

    with patch.object(agent.router, "generate", return_value=mock_result):
        with patch.object(agent.router, "has_any_provider", return_value=True):
            result = agent.generate_post(
                platform="facebook",
                topic="SaaS development",
                goal="Leads",
                tone="Professional",
                language="English",
                cta="Book a call",
            )

    post = db_session.get(Post, result.post_id)
    assert post.input_prompt is not None
    assert post.system_prompt is not None
    assert post.raw_ai_response == json_response
    assert post.provider_used == "openai"
    assert post.provider_latency_ms == 200

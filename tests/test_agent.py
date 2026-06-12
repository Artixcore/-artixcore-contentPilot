"""Tests for ContentPilot agent."""

import pytest

from core.agent import AgentValidationError, ContentPilotAgent
from core.models import Post


def test_mock_provider_generates_valid_post(db_session):
    agent = ContentPilotAgent(db_session)
    result = agent.generate_post(
        platform="facebook",
        topic="SaaS MVP development",
        goal="Drive consultations",
        tone="Professional",
        language="English",
        cta="Book a consultation",
        provider_mode="budget",
    )
    assert result.saved
    assert result.post_id is not None
    assert result.content
    assert result.provider_used == "mock"

    post = db_session.get(Post, result.post_id)
    assert post.status == "pending_approval"


def test_invalid_platform_raises(db_session):
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


def test_empty_topic_raises(db_session):
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


def test_instagram_includes_image_prompt(db_session):
    agent = ContentPilotAgent(db_session)
    result = agent.generate_post(
        platform="instagram",
        topic="AI automation",
        goal="Engagement",
        tone="Visual",
        language="English",
        cta="Visit Artixcore",
        provider_mode="budget",
    )
    assert result.image_prompt

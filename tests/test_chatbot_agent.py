"""Tests for Artixcore chatbot agent."""

from unittest.mock import patch

import pytest

from chatbot.chatbot_agent import ArtixcoreChatbotAgent, CHATBOT_PROVIDER_UNAVAILABLE_MSG, ChatbotAgentError
from chatbot.personality import build_system_prompt
from core.chat_database import get_chatbot_settings, get_or_create_conversation, save_incoming_message
from core.database import get_brand_profile
from core.models import ChatTrainingExample
from providers.base import GenerationResult


def test_blocks_generation_when_no_provider(db_session):
    agent = ArtixcoreChatbotAgent(db_session)
    conv = get_or_create_conversation(db_session, "facebook", user_platform_id="u1", user_display_name="Test")
    user_msg = save_incoming_message(db_session, conv.id, "facebook", "Hello")
    with pytest.raises(ChatbotAgentError, match="Chatbot"):
        agent.generate_reply("facebook", conv.id, "Hello", user_msg.id)


def test_creates_reply_draft_when_provider_available(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    agent = ArtixcoreChatbotAgent(db_session)
    conv = get_or_create_conversation(db_session, "linkedin", user_platform_id="u2", user_display_name="Lead")
    user_msg = save_incoming_message(db_session, conv.id, "linkedin", "What services do you offer?")

    mock_result = GenerationResult(
        text="We build SaaS, web apps, and AI automation for modern businesses.",
        provider="openai",
        model="gpt-4.1-mini",
        latency_ms=100,
    )

    with patch.object(agent.router, "generate", return_value=mock_result):
        with patch.object(agent.router, "has_any_provider", return_value=True):
            reply = agent.generate_reply("linkedin", conv.id, user_msg.message_text, user_msg.id, auto_send=False)

    assert reply.success
    assert reply.draft_text
    assert reply.message_id is not None
    assert reply.reply_status == "pending_approval"


def test_loads_personality_settings(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    settings = get_chatbot_settings(db_session)
    brand = get_brand_profile(db_session)
    prompt = build_system_prompt(settings, brand, "facebook")
    assert settings.chatbot_name in prompt
    assert settings.personality_type in prompt


def test_applies_language_setting(db_session):
    settings = get_chatbot_settings(db_session)
    brand = get_brand_profile(db_session)
    settings.language = "Bangla"
    prompt = build_system_prompt(settings, brand, "facebook")
    assert "Bangla" in prompt


def test_applies_gender_style_safely(db_session):
    settings = get_chatbot_settings(db_session)
    brand = get_brand_profile(db_session)
    settings.gender_style = "Female"
    prompt = build_system_prompt(settings, brand, "twitter")
    assert "Female" in prompt
    assert "stereotypes" in prompt.lower() or "Do not claim" in prompt


def test_saves_conversation_and_training_example(db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    agent = ArtixcoreChatbotAgent(db_session)
    conv = get_or_create_conversation(db_session, "twitter", user_platform_id="u3")
    user_msg = save_incoming_message(db_session, conv.id, "twitter", "Need a CRM system")

    mock_result = GenerationResult(
        text="Happy to help. What features does your CRM need?",
        provider="openai",
        model="gpt-4.1-mini",
    )

    with patch.object(agent.router, "generate", return_value=mock_result):
        with patch.object(agent.router, "has_any_provider", return_value=True):
            reply = agent.generate_reply("twitter", conv.id, user_msg.message_text, user_msg.id, auto_send=False)

    db_session.commit()
    training = (
        db_session.query(ChatTrainingExample)
        .filter(ChatTrainingExample.message_id == reply.message_id)
        .first()
    )
    assert training is not None
    assert training.user_message == "Need a CRM system"

"""Tests for chatbot settings."""

from core.chat_database import get_blocked_keywords, get_chatbot_settings, update_chatbot_settings


def test_default_chatbot_settings_created(db_session):
    settings = get_chatbot_settings(db_session)
    assert settings.chatbot_name == "Artixcore Assistant"
    assert settings.personality_type == "Professional Consultant"
    assert settings.gender_style == "Neutral"
    assert settings.language == "English"
    assert settings.auto_reply_enabled is False
    assert settings.approval_required is True


def test_update_personality(db_session):
    update_chatbot_settings(db_session, personality_type="Technical Expert")
    db_session.commit()
    settings = get_chatbot_settings(db_session)
    assert settings.personality_type == "Technical Expert"


def test_update_gender_style(db_session):
    update_chatbot_settings(db_session, gender_style="Male")
    db_session.commit()
    settings = get_chatbot_settings(db_session)
    assert settings.gender_style == "Male"


def test_update_language(db_session):
    update_chatbot_settings(db_session, language="Hindi")
    db_session.commit()
    settings = get_chatbot_settings(db_session)
    assert settings.language == "Hindi"


def test_blocked_keywords_saved(db_session):
    update_chatbot_settings(db_session, blocked_keywords=["spam", "scam"])
    db_session.commit()
    settings = get_chatbot_settings(db_session)
    assert get_blocked_keywords(settings) == ["spam", "scam"]

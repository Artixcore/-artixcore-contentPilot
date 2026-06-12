"""Tests for chat platform connectors."""

from chatbot.facebook_chat import FacebookChat
from chatbot.linkedin_chat import LinkedInChat
from chatbot.x_chat import XChat
from chatbot.telegram_controller import get_telegram_status, start_telegram_polling


def test_facebook_missing_token_fails_gracefully(monkeypatch):
    monkeypatch.delenv("META_PAGE_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("META_PAGE_ID", raising=False)
    fb = FacebookChat()
    result = fb.send_message("123", "Hello")
    assert result["success"] is False
    assert "token" in result["error"].lower() or "configured" in result["error"].lower()


def test_linkedin_restricted_access_returns_clean_message(monkeypatch):
    monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("LINKEDIN_AUTHOR_URN", "urn:li:person:1")
    monkeypatch.delenv("LINKEDIN_MESSAGING_ENABLED", raising=False)
    li = LinkedInChat()
    status = li.get_status()
    assert status["available"] is False
    result = li.send_message("urn:li:person:2", "Hello")
    assert result["success"] is False
    assert "LinkedIn messaging" in result["error"]


def test_x_missing_token_fails_gracefully(monkeypatch):
    monkeypatch.delenv("X_ACCESS_TOKEN", raising=False)
    x = XChat()
    result = x.send_reply("123", "Hello")
    assert result["success"] is False
    assert "token" in result["error"].lower()


def test_telegram_missing_token_does_not_crash(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    start_telegram_polling()
    status = get_telegram_status()
    assert status["configured"] is False

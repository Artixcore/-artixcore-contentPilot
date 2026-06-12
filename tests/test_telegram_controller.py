"""Tests for Telegram controller admin and commands."""

import asyncio

from core.chat_database import get_chatbot_settings, is_telegram_admin, update_chatbot_settings


class FakeUser:
    def __init__(self, user_id: int):
        self.id = user_id


class FakeMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text: str):
        self.replies.append(text)


class FakeUpdate:
    def __init__(self, user_id: int):
        self.effective_user = FakeUser(user_id)
        self.message = FakeMessage()


class FakeContext:
    def __init__(self, args=None):
        self.args = args or []


def _handlers():
    from chatbot.telegram_controller import _build_handlers

    return {cmd: handler for cmd, handler in _build_handlers()}


def test_unauthorized_user_rejected(db_session, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "111")
    from chatbot.telegram_controller import _reject_unauthorized

    update = FakeUpdate(999)
    context = FakeContext()
    result = asyncio.run(_reject_unauthorized(update, context))
    assert result is False
    assert update.message.replies


def test_authorized_admin_accepted(db_session, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "12345")
    assert is_telegram_admin(db_session, "12345") is True


def test_pause_disables_auto_reply(db_session, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "1")
    update_chatbot_settings(db_session, auto_reply_enabled=True)
    db_session.commit()

    pause_handler = _handlers()["/pause"]
    update = FakeUpdate(1)
    context = FakeContext()
    asyncio.run(pause_handler(update, context))

    settings = get_chatbot_settings(db_session)
    assert settings.auto_reply_enabled is False


def test_resume_enables_auto_reply(db_session, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "1")
    resume_handler = _handlers()["/resume"]
    update = FakeUpdate(1)
    context = FakeContext()
    asyncio.run(resume_handler(update, context))

    settings = get_chatbot_settings(db_session)
    assert settings.auto_reply_enabled is True


def test_mode_approval_enables_approval_mode(db_session, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "1")
    handler = _handlers()["/mode_approval"]
    update = FakeUpdate(1)
    context = FakeContext()
    asyncio.run(handler(update, context))

    settings = get_chatbot_settings(db_session)
    assert settings.approval_required is True
    assert settings.auto_reply_enabled is False


def test_gender_updates_gender_style(db_session, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "1")
    handler = _handlers()["/gender"]
    update = FakeUpdate(1)
    context = FakeContext(["female"])
    asyncio.run(handler(update, context))

    settings = get_chatbot_settings(db_session)
    assert settings.gender_style == "Female"


def test_language_updates_language(db_session, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "1")
    handler = _handlers()["/language"]
    update = FakeUpdate(1)
    context = FakeContext(["Bangla"])
    asyncio.run(handler(update, context))

    settings = get_chatbot_settings(db_session)
    assert settings.language == "Bangla"

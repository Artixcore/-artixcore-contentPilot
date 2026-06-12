"""Chatbot database service layer."""

import json
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.chat_events import log_chat_event
from core.models import (
    DEFAULT_CHATBOT_SETTINGS,
    CHAT_CONVERSATION_STATUSES,
    CHAT_PLATFORMS,
    ChatConversation,
    ChatMessage,
    ChatTrainingExample,
    ChatbotSettings,
    TelegramAdmin,
    TelegramCommand,
)
from core.training_data import export_training_data_jsonl


class ChatDatabaseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _keywords_to_json(keywords: list[str]) -> str:
    return json.dumps(keywords or [])


def _keywords_from_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(k).strip() for k in data if str(k).strip()]
    except json.JSONDecodeError:
        pass
    return []


def seed_default_chatbot_settings(session: Session | None = None) -> ChatbotSettings | None:
    from core.database import get_session

    own_session = session is None
    if own_session:
        session = get_session()
    try:
        existing = session.query(ChatbotSettings).order_by(ChatbotSettings.id.desc()).first()
        if existing:
            return existing
        settings = ChatbotSettings(**DEFAULT_CHATBOT_SETTINGS)
        session.add(settings)
        if own_session:
            session.commit()
            session.refresh(settings)
        else:
            session.flush()
        return settings
    finally:
        if own_session:
            session.close()


def get_chatbot_settings(session: Session) -> ChatbotSettings:
    settings = session.query(ChatbotSettings).order_by(ChatbotSettings.id.desc()).first()
    if not settings:
        settings = seed_default_chatbot_settings(session)
    if not settings:
        raise ChatDatabaseError("Failed to initialize chatbot settings.")
    return settings


def get_or_create_chatbot_settings(session: Session) -> ChatbotSettings:
    return get_chatbot_settings(session)


def update_chatbot_settings(session: Session, **fields: Any) -> ChatbotSettings:
    settings = get_chatbot_settings(session)
    if "blocked_keywords" in fields and isinstance(fields["blocked_keywords"], list):
        fields["blocked_keywords"] = _keywords_to_json(fields["blocked_keywords"])
    for key, value in fields.items():
        if hasattr(settings, key) and value is not None:
            setattr(settings, key, value)
    settings.updated_at = datetime.now(timezone.utc)
    session.flush()
    return settings


def get_blocked_keywords(settings: ChatbotSettings) -> list[str]:
    return _keywords_from_json(settings.blocked_keywords)


def get_or_create_conversation(
    session: Session,
    platform: str,
    user_platform_id: str | None = None,
    user_display_name: str | None = None,
    user_profile_url: str | None = None,
    platform_conversation_id: str | None = None,
) -> ChatConversation:
    platform = (platform or "").strip().lower()
    if platform not in CHAT_PLATFORMS:
        raise ChatDatabaseError(f"Unsupported chat platform: {platform}")

    query = session.query(ChatConversation).filter(ChatConversation.platform == platform)
    if platform_conversation_id:
        query = query.filter(ChatConversation.platform_conversation_id == platform_conversation_id)
    elif user_platform_id:
        query = query.filter(
            ChatConversation.user_platform_id == user_platform_id,
            ChatConversation.status.notin_(("closed", "blocked")),
        )
    else:
        query = query.filter(ChatConversation.id == -1)

    conv = query.order_by(ChatConversation.updated_at.desc()).first()
    if conv:
        if user_display_name:
            conv.user_display_name = user_display_name
        if user_profile_url:
            conv.user_profile_url = user_profile_url
        session.flush()
        return conv

    conv = ChatConversation(
        platform=platform,
        platform_conversation_id=platform_conversation_id or f"local-{platform}-{datetime.now(timezone.utc).timestamp()}",
        user_platform_id=user_platform_id,
        user_display_name=user_display_name or "Guest",
        user_profile_url=user_profile_url,
        status="open",
    )
    session.add(conv)
    session.flush()
    log_chat_event(session, conv.id, "conversation_created", {"platform": platform})
    return conv


def list_conversations(
    session: Session,
    platform: str | None = None,
    status: str | None = None,
    pending_approval: bool = False,
    human_handoff: bool = False,
) -> list[ChatConversation]:
    query = session.query(ChatConversation)
    if platform and platform != "all":
        query = query.filter(ChatConversation.platform == platform)
    if status and status != "all":
        query = query.filter(ChatConversation.status == status)
    if pending_approval:
        query = query.filter(ChatConversation.status == "pending_approval")
    if human_handoff:
        query = query.filter(ChatConversation.status == "human_handoff")
    return query.order_by(ChatConversation.last_message_at.desc().nullslast(), ChatConversation.updated_at.desc()).all()


def update_conversation_status(session: Session, conversation_id: int, status: str) -> ChatConversation:
    if status not in CHAT_CONVERSATION_STATUSES:
        raise ChatDatabaseError(f"Invalid conversation status: {status}")
    conv = session.get(ChatConversation, conversation_id)
    if not conv:
        raise ChatDatabaseError(f"Conversation {conversation_id} not found.")
    conv.status = status
    conv.updated_at = datetime.now(timezone.utc)
    session.flush()
    log_chat_event(session, conversation_id, f"conversation_{status}", {"status": status})
    return conv


def save_incoming_message(
    session: Session,
    conversation_id: int,
    platform: str,
    message_text: str,
    sender_name: str | None = None,
    platform_message_id: str | None = None,
) -> ChatMessage:
    now = datetime.now(timezone.utc)
    msg = ChatMessage(
        conversation_id=conversation_id,
        platform=platform,
        platform_message_id=platform_message_id,
        sender_type="user",
        sender_name=sender_name,
        message_text=message_text,
        message_type="text",
        reply_status="incoming",
    )
    session.add(msg)
    conv = session.get(ChatConversation, conversation_id)
    if conv:
        conv.last_message_at = now
        conv.updated_at = now
        if conv.status == "closed":
            conv.status = "open"
    session.flush()
    log_chat_event(
        session,
        conversation_id,
        "message_received",
        {"message_id": msg.id, "text_preview": message_text[:200]},
        message_id=msg.id,
    )
    return msg


def save_draft_reply(
    session: Session,
    conversation_id: int,
    platform: str,
    user_message_id: int,
    ai_text: str,
    system_prompt: str,
    input_prompt: str,
    raw_ai_response: str,
    provider_used: str,
    model_used: str,
    safety_status: str,
    safety_notes: str | None,
    reply_status: str,
) -> ChatMessage:
    settings = get_chatbot_settings(session)
    msg = ChatMessage(
        conversation_id=conversation_id,
        platform=platform,
        sender_type="bot",
        sender_name=settings.chatbot_name,
        message_text="",
        message_type="text",
        ai_generated_reply=ai_text,
        final_reply=ai_text,
        reply_status=reply_status,
        provider_used=provider_used,
        model_used=model_used,
        system_prompt=system_prompt,
        input_prompt=input_prompt,
        raw_ai_response=raw_ai_response,
        parsed_ai_response=ai_text,
        safety_status=safety_status,
        safety_notes=safety_notes,
    )
    session.add(msg)
    conv = session.get(ChatConversation, conversation_id)
    if conv:
        conv.last_message_at = datetime.now(timezone.utc)
        conv.updated_at = datetime.now(timezone.utc)
        if reply_status == "pending_approval":
            conv.status = "pending_approval"
    session.flush()

    user_msg = session.get(ChatMessage, user_message_id)
    user_text = user_msg.message_text if user_msg else ""

    training = ChatTrainingExample(
        conversation_id=conversation_id,
        message_id=msg.id,
        platform=platform,
        user_message=user_text,
        system_prompt=system_prompt,
        ai_reply=ai_text,
        final_reply=ai_text,
        approval_status=reply_status,
    )
    session.add(training)
    session.flush()
    log_chat_event(
        session,
        conversation_id,
        "ai_reply_generated",
        {"message_id": msg.id, "reply_status": reply_status},
        message_id=msg.id,
    )
    return msg


def get_conversation_messages(session: Session, conversation_id: int) -> list[ChatMessage]:
    return (
        session.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def get_message(session: Session, message_id: int) -> ChatMessage:
    msg = session.get(ChatMessage, message_id)
    if not msg:
        raise ChatDatabaseError(f"Message {message_id} not found.")
    return msg


def count_pending_replies(session: Session) -> int:
    return (
        session.query(func.count(ChatMessage.id))
        .filter(ChatMessage.reply_status == "pending_approval")
        .scalar()
        or 0
    )


def count_open_conversations(session: Session) -> int:
    return (
        session.query(func.count(ChatConversation.id))
        .filter(ChatConversation.status.in_(("open", "pending_approval", "replied")))
        .scalar()
        or 0
    )


def mark_message_sent(session: Session, message_id: int, final_text: str | None = None) -> ChatMessage:
    msg = get_message(session, message_id)
    msg.reply_status = "sent"
    msg.final_reply = final_text or msg.final_reply or msg.ai_generated_reply
    msg.sent_at = datetime.now(timezone.utc)
    msg.updated_at = datetime.now(timezone.utc)

    conv = session.get(ChatConversation, msg.conversation_id)
    if conv:
        conv.status = "replied"
        conv.updated_at = datetime.now(timezone.utc)

    training = (
        session.query(ChatTrainingExample)
        .filter(ChatTrainingExample.message_id == message_id)
        .order_by(ChatTrainingExample.id.desc())
        .first()
    )
    if training:
        training.final_reply = msg.final_reply
        training.approval_status = "sent"

    session.flush()
    log_chat_event(
        session,
        msg.conversation_id,
        "reply_sent",
        {"message_id": message_id},
        message_id=message_id,
    )
    return msg


def reject_message(session: Session, message_id: int, reason: str = "") -> ChatMessage:
    msg = get_message(session, message_id)
    msg.reply_status = "rejected"
    msg.updated_at = datetime.now(timezone.utc)
    if reason:
        msg.safety_notes = f"{msg.safety_notes or ''}\nRejected: {reason}".strip()

    training = (
        session.query(ChatTrainingExample)
        .filter(ChatTrainingExample.message_id == message_id)
        .order_by(ChatTrainingExample.id.desc())
        .first()
    )
    if training:
        training.approval_status = "rejected"

    conv = session.get(ChatConversation, msg.conversation_id)
    if conv and conv.status == "pending_approval":
        conv.status = "open"

    session.flush()
    log_chat_event(
        session,
        msg.conversation_id,
        "reply_rejected",
        {"message_id": message_id, "reason": reason},
        message_id=message_id,
    )
    return msg


def save_manual_reply(
    session: Session,
    conversation_id: int,
    platform: str,
    text: str,
    sender_name: str = "Admin",
) -> ChatMessage:
    msg = ChatMessage(
        conversation_id=conversation_id,
        platform=platform,
        sender_type="human_admin",
        sender_name=sender_name,
        message_text=text,
        message_type="text",
        final_reply=text,
        reply_status="sent",
        sent_at=datetime.now(timezone.utc),
    )
    session.add(msg)
    conv = session.get(ChatConversation, conversation_id)
    if conv:
        conv.last_message_at = datetime.now(timezone.utc)
        conv.status = "replied"
    session.flush()
    log_chat_event(
        session,
        conversation_id,
        "manual_reply_sent",
        {"message_id": msg.id},
        message_id=msg.id,
    )
    return msg


def update_training_feedback(
    session: Session,
    message_id: int,
    human_feedback: str | None = None,
    quality_score: int | None = None,
) -> ChatTrainingExample | None:
    training = (
        session.query(ChatTrainingExample)
        .filter(ChatTrainingExample.message_id == message_id)
        .order_by(ChatTrainingExample.id.desc())
        .first()
    )
    if not training:
        return None
    if human_feedback is not None:
        training.human_feedback = human_feedback
    if quality_score is not None:
        if quality_score < 1 or quality_score > 10:
            raise ChatDatabaseError("Quality score must be between 1 and 10.")
        training.quality_score = quality_score
    training.updated_at = datetime.now(timezone.utc)
    session.flush()
    return training


def get_pending_draft_messages(session: Session, limit: int = 20) -> list[ChatMessage]:
    return (
        session.query(ChatMessage)
        .filter(ChatMessage.reply_status == "pending_approval")
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )


def get_dashboard_stats(session: Session) -> dict:
    settings = get_chatbot_settings(session)
    return {
        "auto_reply_enabled": settings.auto_reply_enabled,
        "approval_required": settings.approval_required,
        "human_handoff_enabled": settings.human_handoff_enabled,
        "pending_replies": count_pending_replies(session),
        "open_conversations": count_open_conversations(session),
        "personality_type": settings.personality_type,
        "gender_style": settings.gender_style,
        "language": settings.language,
    }


def _parse_telegram_admin_ids() -> set[str]:
    raw = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()
    if not raw:
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


def is_telegram_admin(session: Session, telegram_user_id: str | int) -> bool:
    user_id = str(telegram_user_id)
    if user_id in _parse_telegram_admin_ids():
        return True
    admin = (
        session.query(TelegramAdmin)
        .filter(TelegramAdmin.telegram_user_id == user_id, TelegramAdmin.is_active.is_(True))
        .first()
    )
    return admin is not None


def log_telegram_command(
    session: Session,
    telegram_user_id: str | int,
    command: str,
    payload: str | None = None,
    result: str | None = None,
) -> TelegramCommand:
    record = TelegramCommand(
        telegram_user_id=str(telegram_user_id),
        command=command,
        payload=payload,
        result=(result or "")[:2000],
    )
    session.add(record)
    session.flush()
    log_chat_event(
        session,
        0,
        "telegram_command_received",
        {"command": command, "telegram_user_id": str(telegram_user_id)},
    )
    return record


def export_chatbot_training_jsonl(session: Session, include_rejected: bool = False) -> str:
    query = session.query(ChatTrainingExample)
    if not include_rejected:
        query = query.filter(ChatTrainingExample.approval_status != "rejected")
    examples = query.order_by(ChatTrainingExample.created_at.desc()).all()
    settings = get_chatbot_settings(session)
    lines = []
    for ex in examples:
        if not ex.system_prompt or not ex.user_message:
            continue
        output = ex.final_reply or ex.ai_reply or ""
        if not output:
            continue
        record = {
            "messages": [
                {"role": "system", "content": ex.system_prompt},
                {"role": "user", "content": ex.user_message},
                {"role": "assistant", "content": output},
            ],
            "metadata": {
                "platform": ex.platform,
                "personality": settings.personality_type,
                "gender_style": settings.gender_style,
                "language": settings.language,
                "quality_score": ex.quality_score,
                "approval_status": ex.approval_status,
            },
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    return "\n".join(lines) + ("\n" if lines else "")


def export_combined_training_jsonl(session: Session, include_rejected: bool = False) -> str:
    posts_data = export_training_data_jsonl(session, include_rejected=include_rejected)
    chat_data = export_chatbot_training_jsonl(session, include_rejected=include_rejected)
    parts = [p for p in (posts_data.strip(), chat_data.strip()) if p]
    return "\n".join(parts) + ("\n" if parts else "")

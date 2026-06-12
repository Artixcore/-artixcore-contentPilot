"""Channel router for chatbot platform connectors."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from chatbot.facebook_chat import FacebookChat
from chatbot.linkedin_chat import LinkedInChat
from chatbot.schemas import ChannelStatus, IncomingMessage
from chatbot.x_chat import XChat
from chatbot import conversation_service
from core.models import ChatConversation, ChatMessage

logger = logging.getLogger(__name__)

_CHANNELS = {
    "facebook": FacebookChat,
    "linkedin": LinkedInChat,
    "twitter": XChat,
}


def get_chat_channel(platform: str):
    platform = (platform or "").strip().lower()
    cls = _CHANNELS.get(platform)
    if not cls:
        raise ValueError(f"Unsupported chat platform: {platform}")
    return cls()


def get_channel_statuses() -> dict[str, ChannelStatus]:
    statuses = {}
    for name in _CHANNELS:
        channel = get_chat_channel(name)
        status = channel.get_status()
        statuses[name] = ChannelStatus(platform=name, **status)
    return statuses


def receive_message(session: Session, platform: str, payload: dict[str, Any]) -> list[IncomingMessage]:
    platform = (platform or "").strip().lower()
    channel = get_chat_channel(platform)
    results: list[IncomingMessage] = []

    parsed: list[dict] = []
    if platform == "facebook" and hasattr(channel, "parse_webhook_payload"):
        parsed = channel.parse_webhook_payload(payload)
    elif platform == "linkedin" and hasattr(channel, "parse_incoming"):
        parsed = channel.parse_incoming(payload)
    elif payload.get("message_text"):
        parsed = [payload]

    for item in parsed:
        try:
            incoming = conversation_service.receive_incoming_message(
                session,
                platform=platform,
                message_text=item.get("message_text", ""),
                user_name=item.get("user_display_name"),
                user_platform_id=item.get("user_platform_id"),
                user_profile_url=item.get("user_profile_url"),
                platform_conversation_id=item.get("platform_conversation_id"),
                platform_message_id=item.get("platform_message_id"),
            )
            results.append(incoming)
        except Exception as exc:
            logger.warning("Failed to receive %s message: %s", platform, type(exc).__name__)

    session.commit()
    return results


def send_reply(
    session: Session,
    platform: str,
    conversation_id: int,
    message_id: int,
    reply_text: str,
) -> dict:
    platform = (platform or "").strip().lower()
    channel = get_chat_channel(platform)
    conv = session.get(ChatConversation, conversation_id)
    if not conv:
        return {"success": False, "error": f"Conversation {conversation_id} not found."}

    recipient = conv.user_platform_id or conv.platform_conversation_id or ""
    result: dict

    if platform == "facebook":
        result = channel.send_message(recipient, reply_text)
    elif platform == "linkedin":
        result = channel.send_message(recipient, reply_text)
    elif platform == "twitter":
        msg = session.get(ChatMessage, message_id)
        tweet_id = ""
        if msg:
            user_msg = (
                session.query(ChatMessage)
                .filter(
                    ChatMessage.conversation_id == conversation_id,
                    ChatMessage.sender_type == "user",
                )
                .order_by(ChatMessage.id.desc())
                .first()
            )
            if user_msg and user_msg.platform_message_id:
                tweet_id = user_msg.platform_message_id
        result = channel.send_reply(tweet_id, reply_text)
    else:
        result = {"success": False, "error": f"Unsupported platform: {platform}"}

    if result.get("success"):
        from core.chat_database import mark_message_sent

        mark_message_sent(session, message_id, reply_text)
        session.commit()
    else:
        session.rollback()

    return result

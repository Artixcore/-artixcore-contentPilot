"""High-level chatbot conversation orchestration."""

import logging

from sqlalchemy.orm import Session

from chatbot.chatbot_agent import ArtixcoreChatbotAgent, ChatbotAgentError
from chatbot.schemas import ChatReply, IncomingMessage, SimulateMessageRequest
from core.chat_database import (
    get_chatbot_settings,
    get_message,
    list_conversations,
    mark_message_sent,
    reject_message,
    save_incoming_message,
    update_conversation_status,
    update_training_feedback,
    get_dashboard_stats,
    get_or_create_conversation,
)
from core.chat_events import log_chat_event

logger = logging.getLogger(__name__)


def receive_incoming_message(
    session: Session,
    platform: str,
    message_text: str,
    user_name: str | None = None,
    user_platform_id: str | None = None,
    user_profile_url: str | None = None,
    platform_conversation_id: str | None = None,
    platform_message_id: str | None = None,
    generate_reply: bool = True,
    provider_mode: str = "auto",
    selected_provider: str | None = None,
) -> IncomingMessage:
    conv = get_or_create_conversation(
        session,
        platform=platform,
        user_platform_id=user_platform_id,
        user_display_name=user_name,
        user_profile_url=user_profile_url,
        platform_conversation_id=platform_conversation_id,
    )
    user_msg = save_incoming_message(
        session,
        conversation_id=conv.id,
        platform=platform,
        message_text=message_text,
        sender_name=user_name,
        platform_message_id=platform_message_id,
    )

    result = IncomingMessage(
        platform=platform,
        user_platform_id=user_platform_id,
        user_display_name=user_name,
        user_profile_url=user_profile_url,
        platform_conversation_id=conv.platform_conversation_id,
        platform_message_id=platform_message_id,
        message_text=message_text,
        conversation_id=conv.id,
        user_message_id=user_msg.id,
    )

    if conv.status == "human_handoff" or not generate_reply:
        return result

    try:
        agent = ArtixcoreChatbotAgent(session)
        agent.generate_reply(
            platform=platform,
            conversation_id=conv.id,
            user_message=message_text,
            user_message_id=user_msg.id,
            provider_mode=provider_mode,
            selected_provider=selected_provider,
        )
    except ChatbotAgentError as exc:
        logger.warning("Reply generation failed: %s", exc.message)
    except Exception as exc:
        logger.warning("Reply generation error: %s", type(exc).__name__)

    return result


def simulate_incoming_message(session: Session, request: SimulateMessageRequest) -> ChatReply:
    incoming = receive_incoming_message(
        session,
        platform=request.platform,
        message_text=request.message_text,
        user_name=request.user_name,
        user_platform_id=f"sim-{request.user_name.lower().replace(' ', '-')}",
        generate_reply=True,
        provider_mode=request.provider_mode,
        selected_provider=request.selected_provider,
    )
    if incoming.conversation_id:
        from core.chat_database import get_conversation_messages

        messages = get_conversation_messages(session, incoming.conversation_id)
        draft = next(
            (m for m in reversed(messages) if m.sender_type == "bot" and m.reply_status in ("draft", "pending_approval")),
            None,
        )
        if draft:
            return ChatReply(
                success=True,
                conversation_id=incoming.conversation_id,
                message_id=draft.id,
                user_message_id=incoming.user_message_id,
                draft_text=draft.ai_generated_reply or "",
                reply_status=draft.reply_status,
                provider_used=draft.provider_used,
                model_used=draft.model_used,
            )
    return ChatReply(
        success=False,
        conversation_id=incoming.conversation_id or 0,
        user_message_id=incoming.user_message_id,
        error="Reply was not generated. Check AI provider configuration.",
    )


def approve_message(session: Session, message_id: int) -> tuple[bool, str]:
    from chatbot.channel_router import send_reply

    try:
        msg = get_message(session, message_id)
        if msg.reply_status not in ("pending_approval", "draft", "approved"):
            return False, f"Message {message_id} is not pending approval."

        text = msg.final_reply or msg.ai_generated_reply or ""
        if not text.strip():
            return False, "No reply text to send."

        result = send_reply(session, msg.platform, msg.conversation_id, message_id, text)
        if not result.get("success"):
            msg.reply_status = "failed"
            msg.safety_notes = f"{msg.safety_notes or ''}\n{result.get('error', '')}".strip()
            session.flush()
            return False, result.get("error", "Failed to send reply.")

        mark_message_sent(session, message_id, text)
        log_chat_event(
            session,
            msg.conversation_id,
            "reply_approved",
            {"message_id": message_id},
            message_id=message_id,
        )
        session.commit()
        return True, "Reply approved and sent."
    except Exception as exc:
        session.rollback()
        logger.warning("Approve failed: %s", type(exc).__name__)
        return False, "Failed to approve message."


def reject_message_service(session: Session, message_id: int, reason: str = "") -> tuple[bool, str]:
    try:
        reject_message(session, message_id, reason=reason)
        session.commit()
        return True, "Reply rejected."
    except Exception:
        session.rollback()
        return False, "Failed to reject message."


def handoff_conversation(session: Session, conversation_id: int) -> tuple[bool, str]:
    try:
        update_conversation_status(session, conversation_id, "human_handoff")
        log_chat_event(session, conversation_id, "human_handoff_enabled", {})
        session.commit()
        return True, "Conversation marked for human handoff."
    except Exception:
        session.rollback()
        return False, "Failed to update conversation."


def close_conversation(session: Session, conversation_id: int) -> tuple[bool, str]:
    try:
        update_conversation_status(session, conversation_id, "closed")
        log_chat_event(session, conversation_id, "conversation_closed", {})
        session.commit()
        return True, "Conversation closed."
    except Exception:
        session.rollback()
        return False, "Failed to close conversation."


def regenerate_message(
    session: Session,
    message_id: int,
    provider_mode: str = "auto",
    selected_provider: str | None = None,
) -> ChatReply:
    agent = ArtixcoreChatbotAgent(session)
    try:
        reply = agent.regenerate_reply(message_id, provider_mode, selected_provider)
        session.commit()
        return reply
    except ChatbotAgentError as exc:
        session.rollback()
        return ChatReply(success=False, conversation_id=0, error=exc.message)


def save_message_feedback(
    session: Session,
    message_id: int,
    human_feedback: str | None = None,
    quality_score: int | None = None,
) -> tuple[bool, str]:
    try:
        update_training_feedback(session, message_id, human_feedback, quality_score)
        session.commit()
        return True, "Feedback saved."
    except Exception as exc:
        session.rollback()
        return False, getattr(exc, "message", "Failed to save feedback.")

"""Telegram controller bot for chatbot administration."""

import logging
import os
import threading
from typing import Any

from core.chat_database import (
    get_chatbot_settings,
    get_dashboard_stats,
    get_pending_draft_messages,
    is_telegram_admin,
    log_telegram_command,
    update_chatbot_settings,
)
from core.database import session_scope
from core.router import ProviderRouter
from chatbot import conversation_service
from chatbot.chatbot_agent import CHATBOT_PROVIDER_UNAVAILABLE_MSG
from chatbot.channel_router import get_channel_statuses
from chatbot.personality import GENDER_STYLES, LANGUAGES, PERSONALITY_TYPES

logger = logging.getLogger(__name__)

_polling_thread: threading.Thread | None = None
_polling_started = False
_application = None


def _get_admin_ids() -> set[str]:
    raw = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()
    if not raw:
        return set()
    return {p.strip() for p in raw.split(",") if p.strip()}


def get_telegram_status() -> dict:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    admin_ids = _get_admin_ids()
    return {
        "configured": bool(token),
        "running": _polling_started,
        "admin_count": len(admin_ids),
        "token_set": bool(token),
    }


def _is_authorized(session, user_id: int | str) -> bool:
    return is_telegram_admin(session, user_id)


def _log_cmd(session, user_id: int, command: str, payload: str = "", result: str = "") -> None:
    log_telegram_command(session, user_id, command, payload=payload, result=result)
    session.commit()


async def _reject_unauthorized(update: Any, context: Any) -> bool:
    user = update.effective_user
    if not user:
        return False
    with session_scope() as session:
        if not _is_authorized(session, user.id):
            await update.message.reply_text("Unauthorized. This bot is restricted to Artixcore admins.")
            _log_cmd(session, user.id, "unauthorized", result="rejected")
            return False
    return True


def _build_handlers():
    from telegram.ext import Application, CommandHandler, ContextTypes

    async def start_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        with session_scope() as session:
            stats = get_dashboard_stats(session)
            text = (
                "Artixcore ContentPilot Chatbot Controller\n\n"
                f"Auto reply: {'ON' if stats['auto_reply_enabled'] else 'OFF'}\n"
                f"Approval mode: {'ON' if stats['approval_required'] else 'OFF'}\n"
                f"Pending replies: {stats['pending_replies']}\n\n"
                "Use /help for commands."
            )
            await update.message.reply_text(text)
            _log_cmd(session, update.effective_user.id, "/start", result="ok")

    async def status_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        with session_scope() as session:
            router = ProviderRouter(session=session)
            stats = get_dashboard_stats(session)
            channels = get_channel_statuses()
            provider_ok = router.has_any_provider()
            lines = [
                "Chatbot Status",
                f"AI Provider: {'Available' if provider_ok else 'Missing'}",
                f"Auto reply: {'ON' if stats['auto_reply_enabled'] else 'OFF'}",
                f"Approval: {'ON' if stats['approval_required'] else 'OFF'}",
                f"Pending: {stats['pending_replies']}",
                f"Open conversations: {stats['open_conversations']}",
                "",
                "Platforms:",
            ]
            for name, ch in channels.items():
                lines.append(f"- {name}: {ch.message}")
            if not provider_ok:
                lines.append(f"\n{CHATBOT_PROVIDER_UNAVAILABLE_MSG}")
            await update.message.reply_text("\n".join(lines))
            _log_cmd(session, update.effective_user.id, "/status", result="ok")

    async def pause_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        with session_scope() as session:
            update_chatbot_settings(session, auto_reply_enabled=False)
            session.commit()
            await update.message.reply_text("Auto replies paused.")
            _log_cmd(session, update.effective_user.id, "/pause", result="auto_reply_disabled")

    async def resume_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        with session_scope() as session:
            update_chatbot_settings(session, auto_reply_enabled=True)
            session.commit()
            await update.message.reply_text("Auto replies resumed.")
            _log_cmd(session, update.effective_user.id, "/resume", result="auto_reply_enabled")

    async def mode_auto_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        with session_scope() as session:
            update_chatbot_settings(session, auto_reply_enabled=True, approval_required=False)
            session.commit()
            await update.message.reply_text("Mode set to auto reply.")
            _log_cmd(session, update.effective_user.id, "/mode_auto", result="ok")

    async def mode_approval_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        with session_scope() as session:
            update_chatbot_settings(session, auto_reply_enabled=False, approval_required=True)
            session.commit()
            await update.message.reply_text("Mode set to approval required.")
            _log_cmd(session, update.effective_user.id, "/mode_approval", result="ok")

    async def pending_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        with session_scope() as session:
            pending = get_pending_draft_messages(session, limit=10)
            if not pending:
                await update.message.reply_text("No pending replies.")
                _log_cmd(session, update.effective_user.id, "/pending", result="empty")
                return
            lines = ["Pending replies:"]
            for msg in pending:
                preview = (msg.ai_generated_reply or "")[:80]
                lines.append(f"#{msg.id} conv={msg.conversation_id}: {preview}")
            await update.message.reply_text("\n".join(lines))
            _log_cmd(session, update.effective_user.id, "/pending", result=f"count={len(pending)}")

    async def approve_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if not context.args:
            await update.message.reply_text("Usage: /approve {message_id}")
            return
        message_id = int(context.args[0])
        with session_scope() as session:
            ok, msg = conversation_service.approve_message(session, message_id)
            await update.message.reply_text(msg)
            _log_cmd(session, update.effective_user.id, "/approve", str(message_id), msg)

    async def reject_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if not context.args:
            await update.message.reply_text("Usage: /reject {message_id}")
            return
        message_id = int(context.args[0])
        with session_scope() as session:
            ok, msg = conversation_service.reject_message_service(session, message_id)
            await update.message.reply_text(msg)
            _log_cmd(session, update.effective_user.id, "/reject", str(message_id), msg)

    async def reply_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /reply {conversation_id} {message}")
            return
        conv_id = int(context.args[0])
        text = " ".join(context.args[1:])
        with session_scope() as session:
            from core.models import ChatConversation

            conv = session.get(ChatConversation, conv_id)
            if not conv:
                await update.message.reply_text("Conversation not found.")
                return
            from chatbot.channel_router import send_reply
            from chatbot.chatbot_agent import ArtixcoreChatbotAgent

            agent = ArtixcoreChatbotAgent(session)
            msg_id = agent.send_manual_reply(conv_id, conv.platform, text, "Telegram Admin")
            result = send_reply(session, conv.platform, conv_id, msg_id, text)
            await update.message.reply_text("Sent." if result.get("success") else result.get("error", "Failed"))
            _log_cmd(session, update.effective_user.id, "/reply", f"{conv_id} {text[:50]}", str(result.get("success")))

    async def handoff_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if not context.args:
            await update.message.reply_text("Usage: /handoff {conversation_id}")
            return
        conv_id = int(context.args[0])
        with session_scope() as session:
            ok, msg = conversation_service.handoff_conversation(session, conv_id)
            await update.message.reply_text(msg)
            _log_cmd(session, update.effective_user.id, "/handoff", str(conv_id), msg)

    async def close_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if not context.args:
            await update.message.reply_text("Usage: /close {conversation_id}")
            return
        conv_id = int(context.args[0])
        with session_scope() as session:
            ok, msg = conversation_service.close_conversation(session, conv_id)
            await update.message.reply_text(msg)
            _log_cmd(session, update.effective_user.id, "/close", str(conv_id), msg)

    async def personality_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if not context.args:
            await update.message.reply_text(f"Options: {', '.join(PERSONALITY_TYPES)}")
            return
        value = " ".join(context.args)
        with session_scope() as session:
            update_chatbot_settings(session, personality_type=value)
            session.commit()
            await update.message.reply_text(f"Personality set to: {value}")
            _log_cmd(session, update.effective_user.id, "/personality", value, "ok")

    async def gender_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if not context.args:
            await update.message.reply_text("Usage: /gender {male|female|neutral}")
            return
        value = context.args[0].capitalize()
        if value.lower() == "male":
            value = "Male"
        elif value.lower() == "female":
            value = "Female"
        else:
            value = "Neutral"
        with session_scope() as session:
            update_chatbot_settings(session, gender_style=value)
            session.commit()
            await update.message.reply_text(f"Gender style set to: {value}")
            _log_cmd(session, update.effective_user.id, "/gender", value, "ok")

    async def language_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        if not context.args:
            await update.message.reply_text(f"Options: {', '.join(LANGUAGES)}")
            return
        value = " ".join(context.args)
        with session_scope() as session:
            update_chatbot_settings(session, language=value)
            session.commit()
            await update.message.reply_text(f"Language set to: {value}")
            _log_cmd(session, update.effective_user.id, "/language", value, "ok")

    async def help_cmd(update: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _reject_unauthorized(update, context):
            return
        text = (
            "Commands:\n"
            "/start - Welcome\n"
            "/status - Provider and chatbot status\n"
            "/pause - Disable auto replies\n"
            "/resume - Enable auto replies\n"
            "/mode_auto - Auto reply without approval\n"
            "/mode_approval - Approval mode\n"
            "/pending - Pending replies\n"
            "/approve {message_id}\n"
            "/reject {message_id}\n"
            "/reply {conversation_id} {message}\n"
            "/handoff {conversation_id}\n"
            "/close {conversation_id}\n"
            "/personality {type}\n"
            "/gender {male|female|neutral}\n"
            "/language {language}\n"
            "/help - This message"
        )
        await update.message.reply_text(text)
        with session_scope() as session:
            _log_cmd(session, update.effective_user.id, "/help", result="ok")

    return [
        ("/start", start_cmd),
        ("/status", status_cmd),
        ("/pause", pause_cmd),
        ("/resume", resume_cmd),
        ("/mode_auto", mode_auto_cmd),
        ("/mode_approval", mode_approval_cmd),
        ("/pending", pending_cmd),
        ("/approve", approve_cmd),
        ("/reject", reject_cmd),
        ("/reply", reply_cmd),
        ("/handoff", handoff_cmd),
        ("/close", close_cmd),
        ("/personality", personality_cmd),
        ("/gender", gender_cmd),
        ("/language", language_cmd),
        ("/help", help_cmd),
    ]


def start_telegram_polling() -> None:
    global _polling_thread, _polling_started, _application

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logger.info("Telegram bot token not configured; controller disabled.")
        return
    if _polling_started:
        return

    try:
        from telegram.ext import Application
    except ImportError:
        logger.warning("python-telegram-bot not installed; Telegram controller disabled.")
        return

    def _run():
        global _polling_started, _application
        try:
            from telegram.ext import CommandHandler

            app = Application.builder().token(token).build()
            for command, handler in _build_handlers():
                app.add_handler(CommandHandler(command.lstrip("/"), handler))
            _application = app
            _polling_started = True
            logger.info("Starting Telegram controller polling...")
            app.run_polling(drop_pending_updates=True, stop_signals=())
        except Exception as exc:
            logger.warning("Telegram polling failed: %s", type(exc).__name__)
            _polling_started = False

    _polling_thread = threading.Thread(target=_run, daemon=True, name="telegram-controller")
    _polling_thread.start()

"""Chat Control page — chatbot dashboard and primary settings."""

import os

import streamlit as st
from sqlalchemy.orm import Session

from chatbot.chatbot_agent import CHATBOT_PROVIDER_UNAVAILABLE_MSG
from chatbot.channel_router import get_channel_statuses
from chatbot.personality import (
    CTA_STYLES,
    EMOJI_USAGES,
    GENDER_STYLES,
    LANGUAGES,
    PERSONALITY_TYPES,
    REPLY_LENGTHS,
    TONES,
)
from chatbot.telegram_controller import get_telegram_status
from core.chat_database import get_chatbot_settings, get_dashboard_stats, update_chatbot_settings
from core.models import CHAT_PLATFORMS
from core.router import ProviderRouter
from core.utils import format_user_error, mask_secret


def render(session: Session) -> None:
    st.title("Chat Control")
    st.caption("Configure and monitor the Artixcore AI chatbot.")

    router = ProviderRouter(session=session)
    stats = get_dashboard_stats(session)
    settings = get_chatbot_settings(session)
    tg_status = get_telegram_status()
    channels = get_channel_statuses()

    if not router.has_any_provider():
        st.error(CHATBOT_PROVIDER_UNAVAILABLE_MSG)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Auto Reply", "ON" if stats["auto_reply_enabled"] else "OFF")
    c2.metric("Approval Mode", "ON" if stats["approval_required"] else "OFF")
    c3.metric("Human Handoff", "ON" if stats["human_handoff_enabled"] else "OFF")
    c4.metric("Pending Replies", stats["pending_replies"])
    c5.metric("Open Conversations", stats["open_conversations"])
    c6.metric("Telegram", "Running" if tg_status["running"] else ("Ready" if tg_status["configured"] else "Off"))

    st.divider()
    st.subheader("AI Provider Status")
    p1, p2 = st.columns(2)
    availability = router.get_availability_status()
    with p1:
        st.success("OpenAI: Available") if availability.get("openai") else st.warning("OpenAI: Missing")
        st.caption(f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}")
    with p2:
        st.success("Anthropic: Available") if availability.get("anthropic") else st.warning("Anthropic: Missing")
        st.caption(f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}")

    st.divider()
    st.subheader("Platform Connectors")
    for platform in CHAT_PLATFORMS:
        ch = channels.get(platform)
        if ch and ch.configured:
            st.success(f"{platform.title()}: {ch.message}")
        elif ch:
            st.warning(f"{platform.title()}: {ch.message}")
        else:
            st.info(f"{platform.title()}: Not configured")

    st.caption(f"Telegram token: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
    st.caption(f"Telegram admins: {tg_status['admin_count']} configured")

    st.divider()
    st.subheader("Chatbot Behavior")

    auto_reply = st.toggle("Enable Auto Reply", value=settings.auto_reply_enabled)
    approval_required = st.toggle("Require Approval Before Sending", value=settings.approval_required)
    human_handoff = st.toggle("Enable Human Handoff", value=settings.human_handoff_enabled)

    st.subheader("Personality & Style")
    col1, col2 = st.columns(2)
    with col1:
        personality = st.selectbox("Personality Type", PERSONALITY_TYPES, index=PERSONALITY_TYPES.index(settings.personality_type) if settings.personality_type in PERSONALITY_TYPES else 0)
        gender = st.selectbox("Gender Style", GENDER_STYLES, index=GENDER_STYLES.index(settings.gender_style) if settings.gender_style in GENDER_STYLES else 2)
        language = st.selectbox("Language", LANGUAGES, index=LANGUAGES.index(settings.language) if settings.language in LANGUAGES else 0)
    with col2:
        tone = st.selectbox("Tone", TONES, index=TONES.index(settings.tone) if settings.tone in TONES else 0)
        reply_length = st.selectbox("Reply Length", REPLY_LENGTHS, index=REPLY_LENGTHS.index(settings.reply_length) if settings.reply_length in REPLY_LENGTHS else 1)
        emoji_usage = st.selectbox("Emoji Usage", EMOJI_USAGES, index=EMOJI_USAGES.index(settings.emoji_usage) if settings.emoji_usage in EMOJI_USAGES else 1)
        cta_style = st.selectbox("CTA Style", CTA_STYLES, index=CTA_STYLES.index(settings.cta_style) if settings.cta_style in CTA_STYLES else 3)

    if st.button("Save Chat Control Settings", type="primary"):
        try:
            update_chatbot_settings(
                session,
                auto_reply_enabled=auto_reply,
                approval_required=approval_required,
                human_handoff_enabled=human_handoff,
                personality_type=personality,
                gender_style=gender,
                language=language,
                tone=tone,
                reply_length=reply_length,
                emoji_usage=emoji_usage,
                cta_style=cta_style,
            )
            session.commit()
            st.success("Chatbot settings saved.")
            st.rerun()
        except Exception as exc:
            session.rollback()
            st.error(format_user_error("Failed to save settings.", exc))

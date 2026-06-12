"""Chat Control page — chatbot dashboard and settings."""

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
from core.chat_database import get_blocked_keywords, get_chatbot_settings, get_dashboard_stats, update_chatbot_settings
from core.models import CHAT_PLATFORMS
from core.router import ProviderRouter
from core.utils import format_user_error, mask_secret
from ui.bootstrap_components import alert_html, badge, metric_card, section_title, widget_section_header


def _connector_html(name: str, configured: bool, detail: str = "") -> str:
    desc = f'<p class="cp-card-subtitle mb-0 mt-2">{detail}</p>' if detail else ""
    return (
        f'<div class="card border rounded-3 shadow-sm mb-2 p-3">'
        f'<div class="d-flex justify-content-between align-items-start gap-2">'
        f'<span class="fw-semibold">{name}</span>'
        f'{badge("Configured" if configured else "Not Configured", "success" if configured else "warning")}'
        f"</div>{desc}</div>"
    )


def render(session: Session) -> None:
    st.markdown(
        widget_section_header("Chat Control", "Configure and monitor the Artixcore AI chatbot."),
        unsafe_allow_html=True,
    )

    router = ProviderRouter(session=session)
    stats = get_dashboard_stats(session)
    settings = get_chatbot_settings(session)
    tg_status = get_telegram_status()
    channels = get_channel_statuses()
    blocked = get_blocked_keywords(settings)

    if not router.has_any_provider():
        st.markdown(alert_html(CHATBOT_PROVIDER_UNAVAILABLE_MSG, "error"), unsafe_allow_html=True)

    tg_label = "Running" if tg_status["running"] else ("Ready" if tg_status["configured"] else "Off")
    metrics = (
        '<div class="row g-4 mb-3">'
        + metric_card("Auto Reply", "ON" if stats["auto_reply_enabled"] else "OFF", "bi-lightning")
        + metric_card("Approval Mode", "ON" if stats["approval_required"] else "OFF", "bi-check2-square")
        + metric_card("Human Handoff", "ON" if stats["human_handoff_enabled"] else "OFF", "bi-person")
        + metric_card("Pending Replies", stats["pending_replies"], "bi-hourglass")
        + metric_card("Open Conversations", stats["open_conversations"], "bi-chat-dots")
        + metric_card("Telegram", tg_label, "bi-telegram")
        + "</div>"
    )
    st.markdown(metrics, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(section_title("Chatbot Identity"), unsafe_allow_html=True)
            chatbot_name = st.text_input("Chatbot Name", value=settings.chatbot_name, key="cc_name")
            personality = st.selectbox(
                "Personality Type",
                PERSONALITY_TYPES,
                index=PERSONALITY_TYPES.index(settings.personality_type) if settings.personality_type in PERSONALITY_TYPES else 0,
                key="cc_personality",
            )
            gender = st.selectbox(
                "Gender Style",
                GENDER_STYLES,
                index=GENDER_STYLES.index(settings.gender_style) if settings.gender_style in GENDER_STYLES else 2,
                key="cc_gender",
            )
            language = st.selectbox(
                "Language",
                LANGUAGES,
                index=LANGUAGES.index(settings.language) if settings.language in LANGUAGES else 0,
                key="cc_language",
            )
            custom_personality = st.text_area(
                "Custom Personality Prompt",
                value=settings.custom_personality_prompt or "",
                key="cc_custom",
            )
        with st.container(border=True):
            st.markdown(section_title("Behavior"), unsafe_allow_html=True)
            auto_reply = st.toggle("Enable Auto Reply", value=settings.auto_reply_enabled, key="cc_auto")
            approval_required = st.toggle("Require Approval Before Sending", value=settings.approval_required, key="cc_approval")
            human_handoff = st.toggle("Enable Human Handoff", value=settings.human_handoff_enabled, key="cc_handoff")
            tone = st.selectbox(
                "Tone",
                TONES,
                index=TONES.index(settings.tone) if settings.tone in TONES else 0,
                key="cc_tone",
            )
            reply_length = st.selectbox(
                "Reply Length",
                REPLY_LENGTHS,
                index=REPLY_LENGTHS.index(settings.reply_length) if settings.reply_length in REPLY_LENGTHS else 1,
                key="cc_length",
            )
            emoji_usage = st.selectbox(
                "Emoji Usage",
                EMOJI_USAGES,
                index=EMOJI_USAGES.index(settings.emoji_usage) if settings.emoji_usage in EMOJI_USAGES else 1,
                key="cc_emoji",
            )
            cta_style = st.selectbox(
                "CTA Style",
                CTA_STYLES,
                index=CTA_STYLES.index(settings.cta_style) if settings.cta_style in CTA_STYLES else 3,
                key="cc_cta",
            )
    with col2:
        with st.container(border=True):
            st.markdown(section_title("Safety"), unsafe_allow_html=True)
            blocked_keywords = st.text_area(
                "Blocked Keywords (one per line)",
                value="\n".join(blocked),
                key="cc_blocked",
            )
            fallback_message = st.text_area(
                "Fallback Message",
                value=settings.fallback_message or "",
                key="cc_fallback",
            )
            business_hours_enabled = st.toggle(
                "Enable Business Hours",
                value=settings.business_hours_enabled,
                key="cc_bh_enabled",
            )
            bh1, bh2 = st.columns(2)
            with bh1:
                business_hours_start = st.text_input(
                    "Start (HH:MM UTC)",
                    value=settings.business_hours_start or "09:00",
                    key="cc_bh_start",
                )
            with bh2:
                business_hours_end = st.text_input(
                    "End (HH:MM UTC)",
                    value=settings.business_hours_end or "17:00",
                    key="cc_bh_end",
                )
        with st.container(border=True):
            st.markdown(section_title("Telegram Controller"), unsafe_allow_html=True)
            tg_configured = tg_status.get("configured", False)
            st.markdown(
                _connector_html(
                    "Telegram Bot",
                    tg_configured,
                    f"Status: {'Running' if tg_status.get('running') else 'Ready' if tg_configured else 'Off'}",
                ),
                unsafe_allow_html=True,
            )
            st.caption(f"Token: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
            st.caption(f"Admin IDs: {tg_status['admin_count']} configured")
            st.caption(f"Pending replies: {stats['pending_replies']}")
        with st.container(border=True):
            st.markdown(section_title("Platform Connectors"), unsafe_allow_html=True)
            availability = router.get_availability_status()
            connectors = [
                _connector_html("OpenAI", bool(availability.get("openai")), mask_secret(os.getenv("OPENAI_API_KEY", ""))),
                _connector_html("Anthropic", bool(availability.get("anthropic")), mask_secret(os.getenv("ANTHROPIC_API_KEY", ""))),
            ]
            for platform in CHAT_PLATFORMS:
                ch = channels.get(platform)
                configured = bool(ch and ch.configured)
                connectors.append(_connector_html(platform.title(), configured, ch.message if ch else "Not configured"))
            st.markdown("".join(connectors), unsafe_allow_html=True)

    if st.button("Save Chat Control Settings", type="primary", use_container_width=True):
        try:
            keywords = [k.strip() for k in blocked_keywords.splitlines() if k.strip()]
            update_chatbot_settings(
                session,
                chatbot_name=chatbot_name,
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
                custom_personality_prompt=custom_personality or None,
                blocked_keywords=keywords,
                fallback_message=fallback_message or None,
                business_hours_enabled=business_hours_enabled,
                business_hours_start=business_hours_start or None,
                business_hours_end=business_hours_end or None,
            )
            session.commit()
            st.success("Chatbot settings saved.")
            st.rerun()
        except Exception as exc:
            session.rollback()
            st.markdown(alert_html(format_user_error("Failed to save settings.", exc), "error"), unsafe_allow_html=True)

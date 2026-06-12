"""Integrations overview page — combined connector status."""

import os

import streamlit as st
from sqlalchemy.orm import Session

from chatbot.channel_router import get_channel_statuses
from chatbot.telegram_controller import get_telegram_status
from core.models import CHAT_PLATFORMS
from core.publishing import get_publisher_statuses
from core.router import ProviderRouter
from core.utils import mask_secret
from ui.bootstrap_components import badge, section_title, widget_section_header
from ui.navigation import navigate


def _status_card(name: str, configured: bool, detail: str = "") -> str:
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
        widget_section_header("Integrations", "Provider, publishing, and chat connector status at a glance."),
        unsafe_allow_html=True,
    )

    router = ProviderRouter(session=session)
    availability = router.get_availability_status()
    pub_statuses = get_publisher_statuses()
    channels = get_channel_statuses()
    tg_status = get_telegram_status()

    st.markdown(section_title("AI Providers"), unsafe_allow_html=True)
    st.markdown(
        _status_card("OpenAI", bool(availability.get("openai")), f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}")
        + _status_card("Anthropic", bool(availability.get("anthropic")), f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}"),
        unsafe_allow_html=True,
    )

    st.markdown(section_title("Publishing Connectors"), unsafe_allow_html=True)
    pub_labels = {
        "linkedin": "LinkedIn",
        "twitter": "X / Twitter",
        "facebook": "Facebook Page",
        "instagram": "Instagram",
        "website_blog": "Website API",
    }
    st.markdown(
        "".join(_status_card(label, pub_statuses.get(key, False)) for key, label in pub_labels.items()),
        unsafe_allow_html=True,
    )

    st.markdown(section_title("Chat Platforms"), unsafe_allow_html=True)
    chat_cards = ""
    for platform in CHAT_PLATFORMS:
        ch = channels.get(platform)
        configured = bool(ch and ch.configured)
        detail = ch.message if ch else "Not configured"
        chat_cards += _status_card(platform.title(), configured, detail)
    st.markdown(chat_cards, unsafe_allow_html=True)

    st.markdown(
        _status_card(
            "Telegram Controller",
            tg_status.get("configured", False),
            f"Status: {'Running' if tg_status.get('running') else 'Ready' if tg_status.get('configured') else 'Off'} · "
            f"Admins: {tg_status.get('admin_count', 0)}",
        ),
        unsafe_allow_html=True,
    )

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Provider Settings", key="int_prov", use_container_width=True):
            navigate("provider_settings")
    with c2:
        if st.button("Publishing Settings", key="int_pub", use_container_width=True):
            navigate("publishing_settings")
    with c3:
        if st.button("Chat Control", key="int_chat", use_container_width=True):
            navigate("chat_control")

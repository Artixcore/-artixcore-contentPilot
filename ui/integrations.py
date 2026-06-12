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
from ui.components import render_connector_status, render_page_header, render_section_header
from ui.navigation import navigate


def render(session: Session) -> None:
    render_page_header("Integrations", "Provider, publishing, and chat connector status at a glance.")

    router = ProviderRouter(session=session)
    availability = router.get_availability_status()
    pub_statuses = get_publisher_statuses()
    channels = get_channel_statuses()
    tg_status = get_telegram_status()

    render_section_header("AI Providers")
    c1, c2 = st.columns(2)
    with c1:
        render_connector_status(
            "OpenAI",
            bool(availability.get("openai")),
            f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}",
        )
    with c2:
        render_connector_status(
            "Anthropic",
            bool(availability.get("anthropic")),
            f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}",
        )

    render_section_header("Publishing Connectors")
    pub_labels = {
        "linkedin": "LinkedIn",
        "twitter": "X / Twitter",
        "facebook": "Facebook Page",
        "instagram": "Instagram",
        "website_blog": "Website API",
    }
    for key, label in pub_labels.items():
        render_connector_status(label, pub_statuses.get(key, False))

    render_section_header("Chat Platforms")
    for platform in CHAT_PLATFORMS:
        ch = channels.get(platform)
        configured = bool(ch and ch.configured)
        detail = ch.message if ch else "Not configured"
        render_connector_status(platform.title(), configured, detail)

    render_connector_status(
        "Telegram Controller",
        tg_status.get("configured", False),
        f"Status: {'Running' if tg_status.get('running') else 'Ready' if tg_status.get('configured') else 'Off'} · "
        f"Admins: {tg_status.get('admin_count', 0)}",
    )

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Provider Settings", key="int_prov", use_container_width=True):
            navigate("provider_settings")
            st.rerun()
    with c2:
        if st.button("Publishing Settings", key="int_pub", use_container_width=True):
            navigate("publishing_settings")
            st.rerun()
    with c3:
        if st.button("Chat Control", key="int_chat", use_container_width=True):
            navigate("chat_control")
            st.rerun()

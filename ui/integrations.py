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
from ui.components import connector_row, page_header, section_title
from ui.navigation import navigate


def render(session: Session) -> None:
    page_header("Integrations", "Provider, publishing, and chat connector status at a glance.")

    router = ProviderRouter(session=session)
    availability = router.get_availability_status()
    pub_statuses = get_publisher_statuses()
    channels = get_channel_statuses()
    tg_status = get_telegram_status()

    section_title("AI Providers")
    connector_row("OpenAI", bool(availability.get("openai")), f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}")
    connector_row("Anthropic", bool(availability.get("anthropic")), f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}")

    section_title("Publishing Connectors")
    pub_labels = {
        "linkedin": "LinkedIn",
        "twitter": "X / Twitter",
        "facebook": "Facebook Page",
        "instagram": "Instagram",
        "website_blog": "Website API",
    }
    for key, label in pub_labels.items():
        connector_row(label, pub_statuses.get(key, False))

    section_title("Chat Platforms")
    for platform in CHAT_PLATFORMS:
        ch = channels.get(platform)
        configured = bool(ch and ch.configured)
        connector_row(platform.title(), configured, ch.message if ch else "Not configured")

    connector_row(
        "Telegram Controller",
        tg_status.get("configured", False),
        f"Status: {'Running' if tg_status.get('running') else 'Ready' if tg_status.get('configured') else 'Off'} · "
        f"Admins: {tg_status.get('admin_count', 0)}",
    )

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Provider Settings", key="int_prov", use_container_width=True):
            navigate("Provider Settings")
    with c2:
        if st.button("Publishing Settings", key="int_pub", use_container_width=True):
            navigate("Publishing Settings")
    with c3:
        if st.button("Chat Control", key="int_chat", use_container_width=True):
            navigate("Chat Control")

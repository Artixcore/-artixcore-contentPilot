"""Navigation state helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st

ICON_RAIL: list[tuple[str, str, str]] = [
    ("dashboard", "⌂", "Dashboard"),
    ("ai_workspace", "✦", "Content Agent"),
    ("chat_inbox", "💬", "Chatbot"),
    ("publish_center", "↗", "Social Publishing"),
    ("training_data", "◎", "Training Data"),
    ("integrations", "⚡", "Integrations"),
    ("chat_control", "⚙", "Settings"),
]

SIDEBAR_PRIMARY: list[tuple[str, str]] = [
    ("dashboard", "Dashboard"),
    ("ai_workspace", "AI Workspace"),
    ("create_post", "Create Post"),
    ("chat_inbox", "Chat Inbox"),
    ("publish_center", "Publish Center"),
    ("campaigns", "Campaigns"),
]

SIDEBAR_WORKSPACES: list[str] = [
    "Artixcore",
    "Dealzyro",
    "Digitalplanup",
    "ContentPilot",
    "General",
]

SIDEBAR_SYSTEM: list[tuple[str, str]] = [
    ("brand_settings", "Brand Settings"),
    ("provider_settings", "Provider Settings"),
    ("publishing_settings", "Publishing Settings"),
    ("chat_control", "Chat Control"),
    ("training_data", "Training Data"),
    ("exports", "Exports"),
]

PAGE_LABELS: dict[str, str] = {
    "dashboard": "Dashboard",
    "ai_workspace": "AI Workspace",
    "create_post": "Create Post",
    "chat_inbox": "Chat Inbox",
    "publish_center": "Publish Center",
    "campaigns": "Campaigns",
    "approvals": "Approvals",
    "chat_control": "Chat Control",
    "training_data": "Training Data",
    "integrations": "Integrations",
    "brand_settings": "Brand Settings",
    "provider_settings": "Provider Settings",
    "publishing_settings": "Publishing Settings",
    "exports": "Exports",
}


def init_navigation() -> None:
    defaults: dict[str, Any] = {
        "nav_page": "dashboard",
        "sidebar_open": True,
        "active_workspace": "Artixcore",
        "chat_messages": [],
        "workspace_mode": "welcome",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate(page_key: str) -> None:
    st.session_state.nav_page = page_key


def get_current_page_label() -> str:
    return PAGE_LABELS.get(st.session_state.nav_page, "Dashboard")

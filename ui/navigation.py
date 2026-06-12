"""Navigation state helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st

NAV_OPTIONS: list[tuple[str, str]] = [
    ("Dashboard", "dashboard"),
    ("AI Workspace", "ai_workspace"),
    ("Create Post", "create_post"),
    ("Approvals", "approvals"),
    ("Chat Inbox", "chat_inbox"),
    ("Chat Control", "chat_control"),
    ("Publish Center", "publish_center"),
    ("Campaigns", "campaigns"),
    ("Training Data", "training_data"),
    ("Provider Settings", "provider_settings"),
    ("Publishing Settings", "publishing_settings"),
    ("Brand Settings", "brand_settings"),
    ("Integrations", "integrations"),
    ("Exports", "exports"),
]

NAV_LABELS = [label for label, _ in NAV_OPTIONS]
NAV_KEYS = [key for _, key in NAV_OPTIONS]

SIDEBAR_WORKSPACES: list[str] = [
    "Artixcore",
    "Dealzyro",
    "Digitalplanup",
    "General",
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
        "active_workspace": "Artixcore",
        "chat_messages": [],
        "workspace_mode": "welcome",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate(page_key: str) -> None:
    st.session_state.nav_page = page_key
    st.query_params["view"] = page_key
    st.rerun()


def sync_view_from_query(pages: dict) -> tuple[str, str]:
    """Read view/workspace from query params and sync session state."""
    view = st.query_params.get("view", "dashboard")
    if view not in pages:
        view = "dashboard"
    st.session_state.nav_page = view

    workspace = st.query_params.get("workspace", st.session_state.get("active_workspace", "Artixcore"))
    if workspace not in SIDEBAR_WORKSPACES:
        workspace = "Artixcore"
    st.session_state.active_workspace = workspace
    return view, workspace


def get_current_page_label() -> str:
    return PAGE_LABELS.get(st.session_state.nav_page, "Dashboard")


def label_for_key(page_key: str) -> str:
    return PAGE_LABELS.get(page_key, "Dashboard")


def key_for_label(label: str) -> str:
    for nav_label, key in NAV_OPTIONS:
        if nav_label == label:
            return key
    return "dashboard"


def current_nav_label() -> str:
    return label_for_key(st.session_state.nav_page)

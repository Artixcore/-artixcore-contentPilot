"""Navigation state helpers."""

from __future__ import annotations

import streamlit as st

NAV_OPTIONS: list[tuple[str, str]] = [
    ("Dashboard", "dashboard"),
    ("AI Workspace", "ai_workspace"),
    ("Create Post", "create_post"),
    ("Approvals", "approvals"),
    ("Chat Inbox", "chat_inbox"),
    ("Chat Control", "chat_control"),
    ("Publish Center", "publish_center"),
    ("Training Data", "training_data"),
    ("Provider Settings", "provider_settings"),
    ("Publishing Settings", "publishing_settings"),
    ("Brand Settings", "brand_settings"),
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

PAGE_LABELS: dict[str, str] = {key: label for label, key in NAV_OPTIONS}

PAGE_SUBTITLES: dict[str, str] = {
    "dashboard": "Overview of your content pipeline, chatbot activity, publishing connectors, and system health.",
    "ai_workspace": "Ask ContentPilot to create, reply, plan, or publish.",
    "create_post": "Generate AI-powered content for your selected platform.",
    "approvals": "Review, edit, approve, or reject pending content. No auto-publishing.",
    "chat_inbox": "Review conversations, approve AI replies, and simulate incoming messages.",
    "chat_control": "Configure and monitor the Artixcore AI chatbot.",
    "publish_center": "Publish approved or scheduled posts. Human confirmation required.",
    "training_data": "Manage training examples for fine-tuning, RAG, and brand learning.",
    "provider_settings": "AI provider status and configuration.",
    "publishing_settings": "Social platform connector status. Tokens loaded from `.env`.",
    "brand_settings": "Configure the Artixcore brand profile used for content generation.",
    "exports": "Download posts, training data, and activity logs.",
}


def init_navigation() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "active_workspace" not in st.session_state:
        st.session_state.active_workspace = "Artixcore"


def navigate(page_label: str) -> None:
    """Switch to a page by display label."""
    st.session_state["page"] = page_label
    st.session_state["page_radio"] = page_label
    st.rerun()


def label_for_key(page_key: str) -> str:
    return PAGE_LABELS.get(page_key, "Dashboard")


def key_for_label(label: str) -> str:
    for nav_label, key in NAV_OPTIONS:
        if nav_label == label:
            return key
    return "dashboard"

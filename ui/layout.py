"""App shell layout, navigation, and page registry."""

from __future__ import annotations

from collections.abc import Callable
import streamlit as st
from sqlalchemy.orm import Session

from ui import (
    ai_workspace,
    approvals,
    brand_settings,
    campaigns,
    chat_control,
    chat_inbox,
    create_post,
    dashboard,
    exports,
    integrations,
    provider_settings,
    publish_center,
    publishing_settings,
    training_data,
)
from ui.components import render_upgrade_card
from ui.navigation import get_current_page_label, init_navigation, navigate
from ui.theme import PRIMARY, TEXT_MUTED, TEXT_PRIMARY

PageRenderer = Callable[[Session], None]

PAGES: dict[str, PageRenderer] = {
    "dashboard": dashboard.render,
    "ai_workspace": ai_workspace.render,
    "create_post": create_post.render,
    "chat_inbox": chat_inbox.render,
    "publish_center": publish_center.render,
    "campaigns": campaigns.render,
    "approvals": approvals.render,
    "chat_control": chat_control.render,
    "training_data": training_data.render,
    "integrations": integrations.render,
    "brand_settings": brand_settings.render,
    "provider_settings": provider_settings.render,
    "publishing_settings": publishing_settings.render,
    "exports": exports.render,
}

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


def _nav_button(key: str, label: str, css_class: str = "cp-sidebar-nav") -> None:
    active = st.session_state.nav_page == key
    wrap_cls = f"{css_class}{' active' if active else ''}"
    st.markdown(f'<div class="{wrap_cls}">', unsafe_allow_html=True)
    if st.button(label, key=f"nav_{key}", use_container_width=True):
        navigate(key)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_icon_rail() -> None:
    for page_key, icon, tooltip in ICON_RAIL:
        active = st.session_state.nav_page == page_key
        wrap_cls = f"cp-nav-btn-wrap{' active' if active else ''}"
        st.markdown(f'<div class="{wrap_cls}" title="{tooltip}">', unsafe_allow_html=True)
        if st.button(icon, key=f"rail_{page_key}", help=tooltip):
            navigate(page_key)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> None:
    collapsed = not st.session_state.sidebar_open
    display = "none" if collapsed else "flex"
    st.markdown(
        f"""
        <div style="display:{display};flex-direction:column;height:100%;">
            <div style="font-weight:700;font-size:1.125rem;color:{TEXT_PRIMARY};margin-bottom:4px;">
                Artixcore Pilot
            </div>
            <div style="font-size:0.75rem;color:{TEXT_MUTED};margin-bottom:16px;">ContentPilot</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("+ New Content", key="sidebar_new", type="primary", use_container_width=True):
            navigate("create_post")
            st.rerun()
    with c2:
        if st.button("Import", key="sidebar_import", use_container_width=True):
            navigate("ai_workspace")
            st.rerun()

    st.text_input("Search", placeholder="Search...", key="sidebar_search", label_visibility="collapsed")

    st.markdown('<div class="cp-section-title">Primary</div>', unsafe_allow_html=True)
    for page_key, label in SIDEBAR_PRIMARY:
        _nav_button(page_key, label)

    st.markdown('<div class="cp-section-title">Works / Projects</div>', unsafe_allow_html=True)
    for ws in SIDEBAR_WORKSPACES:
        active = st.session_state.active_workspace == ws
        style = f"background:#FFF7ED;color:{PRIMARY};font-weight:600;" if active else ""
        st.markdown(
            f'<div class="cp-nav-item cp-workspace-item" style="{style}">',
            unsafe_allow_html=True,
        )
        if st.button(ws, key=f"ws_{ws}", use_container_width=True):
            st.session_state.active_workspace = ws
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="cp-section-title">System</div>', unsafe_allow_html=True)
    for page_key, label in SIDEBAR_SYSTEM:
        _nav_button(page_key, label)

    st.markdown(render_upgrade_card(), unsafe_allow_html=True)
    if st.button("Upgrade Premium", key="upgrade_btn", type="primary", use_container_width=True):
        st.toast("Premium upgrade coming soon.")


def render_topbar() -> None:
    page_label = get_current_page_label()
    left_cols = st.columns([0.08, 0.5, 0.42])
    with left_cols[0]:
        st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
        if st.button("☰", key="toggle_sidebar", help="Toggle sidebar"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with left_cols[1]:
        st.markdown(
            f'<div style="font-weight:600;color:{TEXT_PRIMARY};padding-top:8px;">{page_label}</div>',
            unsafe_allow_html=True,
        )
    with left_cols[2]:
        tc = st.columns([1, 1, 1, 1, 1])
        with tc[0]:
            st.markdown('<div class="cp-topbar-btn">', unsafe_allow_html=True)
            if st.button("Upgrade Plan", key="top_upgrade"):
                st.toast("Premium upgrade coming soon.")
            st.markdown("</div>", unsafe_allow_html=True)
        with tc[1]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            st.button("🕐", key="top_history", help="History")
            st.markdown("</div>", unsafe_allow_html=True)
        with tc[2]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            st.button("↗", key="top_share", help="Share")
            st.markdown("</div>", unsafe_allow_html=True)
        with tc[3]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            st.button("🔔", key="top_notify", help="Notifications")
            st.markdown("</div>", unsafe_allow_html=True)
        with tc[4]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            if st.button("👤", key="top_profile", help="Profile"):
                navigate("brand_settings")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def render_app_shell(session: Session) -> None:
    """Render navigation shell and current page content."""
    init_navigation()

    ratios = [0.045, 0.165, 0.79] if st.session_state.sidebar_open else [0.045, 0.955]
    shell = st.columns(ratios)
    sidebar_visible = st.session_state.sidebar_open

    with shell[0]:
        st.markdown('<div class="cp-shell-rail">', unsafe_allow_html=True)
        render_icon_rail()
        st.markdown("</div>", unsafe_allow_html=True)

    main_idx = 2 if sidebar_visible else 1

    if sidebar_visible:
        with shell[1]:
            st.markdown('<div class="cp-shell-sidebar">', unsafe_allow_html=True)
            render_sidebar()
            st.markdown("</div>", unsafe_allow_html=True)

    with shell[main_idx]:
        st.markdown('<div class="cp-shell-main">', unsafe_allow_html=True)
        render_topbar()
        st.markdown('<div class="cp-content-area">', unsafe_allow_html=True)
        page_key = st.session_state.nav_page
        renderer = PAGES.get(page_key, dashboard.render)
        renderer(session)
        st.markdown("</div></div>", unsafe_allow_html=True)

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
from ui.components import render_icon_rail, render_sidebar, render_topbar
from ui.navigation import init_navigation

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


def render_app_shell(session: Session) -> None:
    """Render navigation shell and current page content."""
    init_navigation()

    st.markdown('<div class="cp-page-bg">', unsafe_allow_html=True)

    sidebar_visible = st.session_state.sidebar_open
    if sidebar_visible:
        shell = st.columns([0.041, 0.179, 0.78], gap="small")
    else:
        shell = st.columns([0.041, 0.959], gap="small")

    with shell[0]:
        st.markdown('<div class="cp-shell-rail cp-icon-rail">', unsafe_allow_html=True)
        render_icon_rail()
        st.markdown("</div>", unsafe_allow_html=True)

    main_idx = 2 if sidebar_visible else 1

    if sidebar_visible:
        with shell[1]:
            st.markdown('<div class="cp-shell-sidebar cp-sidebar">', unsafe_allow_html=True)
            render_sidebar()
            st.markdown("</div>", unsafe_allow_html=True)

    with shell[main_idx]:
        st.markdown('<div class="cp-shell-main cp-main">', unsafe_allow_html=True)
        render_topbar()
        st.markdown('<div class="cp-content-area"><div class="cp-content-inner">', unsafe_allow_html=True)
        page_key = st.session_state.nav_page
        renderer = PAGES.get(page_key, dashboard.render)
        renderer(session)
        st.markdown("</div></div></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

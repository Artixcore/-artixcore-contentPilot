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
from ui.components import render_sidebar, render_topbar
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
    render_sidebar()
    render_topbar()
    st.divider()

    page_key = st.session_state.nav_page
    renderer = PAGES.get(page_key, dashboard.render)
    renderer(session)

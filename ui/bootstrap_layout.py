"""Bootstrap app shell layout and query-param page routing."""

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
from ui.bootstrap_components import chrome_only
from ui.navigation import init_navigation, label_for_key, sync_view_from_query

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
    """Render Bootstrap chrome and current page content."""
    init_navigation()
    view, workspace = sync_view_from_query(PAGES)
    page_title = label_for_key(view)

    st.markdown(chrome_only(view, page_title, workspace), unsafe_allow_html=True)

    renderer = PAGES.get(view, dashboard.render)
    renderer(session)

"""Bootstrap app shell layout and query-param page routing."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st
from sqlalchemy.orm import Session

from core.error_handler import log_exception
from core.utils import APP_DEBUG, format_user_error
from ui import (
    ai_workspace,
    approvals,
    brand_settings,
    chat_control,
    chat_inbox,
    create_post,
    dashboard,
    exports,
    provider_settings,
    publish_center,
    publishing_settings,
    training_data,
)
from ui.bootstrap_components import app_shell, error_card, page_header
from ui.navigation import PAGE_SUBTITLES, init_navigation, label_for_key, sync_view_from_query

PageRenderer = Callable[[Session], None]

PAGES: dict[str, PageRenderer] = {
    "dashboard": dashboard.render,
    "ai_workspace": ai_workspace.render,
    "create_post": create_post.render,
    "chat_inbox": chat_inbox.render,
    "publish_center": publish_center.render,
    "approvals": approvals.render,
    "chat_control": chat_control.render,
    "training_data": training_data.render,
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

    try:
        if view == "dashboard":
            page_html = dashboard.render_html(session)
            st.markdown(
                app_shell(view, page_html, page_title, workspace),
                unsafe_allow_html=True,
            )
        elif view == "ai_workspace":
            static_html = ai_workspace.render_static_html(session)
            st.markdown(
                app_shell(view, static_html, page_title, workspace),
                unsafe_allow_html=True,
            )
            ai_workspace.render_widgets(session)
        else:
            subtitle = PAGE_SUBTITLES.get(view)
            header_html = page_header(page_title, subtitle)
            st.markdown(
                app_shell(view, header_html, page_title, workspace),
                unsafe_allow_html=True,
            )
            PAGES[view](session)
    except Exception as exc:
        log_exception(exc, context=f"page:{view}")
        safe_reason = format_user_error("", exc) if APP_DEBUG else None
        error_html = error_card(
            "UI rendering error",
            "Something went wrong while rendering this page.",
            safe_reason,
            "Refresh the page or check the logs.",
        )
        st.markdown(
            app_shell(view, error_html, page_title, workspace),
            unsafe_allow_html=True,
        )

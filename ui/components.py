"""Reusable UI components for Artixcore ContentPilot."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ui.navigation import (
    NAV_LABELS,
    SIDEBAR_WORKSPACES,
    current_nav_label,
    key_for_label,
    navigate,
)
from ui.theme import TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY


def _esc(text: str | None) -> str:
    return html.escape(str(text or ""))


def render_page_header(title: str, subtitle: str | None = None) -> None:
    sub = f'<p class="cp-page-subtitle">{_esc(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<h1 class="cp-page-title">{_esc(title)}</h1>{sub}',
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(
        f'<div class="cp-section-label">{_esc(title)}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<p style="font-size:0.875rem;color:{TEXT_SECONDARY};margin:-8px 0 14px 0;">{_esc(subtitle)}</p>',
            unsafe_allow_html=True,
        )


def render_section_header(title: str) -> None:
    """Backward-compatible alias."""
    render_section_title(title)


def render_card(
    title: str | None = None,
    subtitle: str | None = None,
    body_html: str | None = None,
    class_name: str = "",
    *,
    content_html: str | None = None,
    panel: bool = False,
) -> None:
    if content_html is not None:
        cls = "cp-card-panel" if panel else "cp-card"
        st.markdown(f'<div class="{cls}">{content_html}</div>', unsafe_allow_html=True)
        return

    extra = f" {class_name}" if class_name else ""
    cls = f"cp-card{extra}"
    title_html = f'<div class="cp-card-title">{_esc(title)}</div>' if title else ""
    sub_html = f'<div class="cp-card-subtitle">{_esc(subtitle)}</div>' if subtitle else ""
    body = body_html or ""
    st.markdown(
        f'<div class="{cls}">{title_html}{sub_html}{body}</div>',
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str | int, icon: str = "📊") -> None:
    st.markdown(
        f"""
        <div class="cp-metric-card">
            <div class="cp-metric-icon">{icon}</div>
            <div class="cp-metric-label">{_esc(label)}</div>
            <div class="cp-metric-value">{_esc(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(label: str, status: str = "muted") -> str:
    kind_map = {
        "success": "cp-badge-success",
        "configured": "cp-badge-success",
        "approved": "cp-badge-success",
        "published": "cp-badge-success",
        "healthy": "cp-badge-success",
        "warning": "cp-badge-warning",
        "pending": "cp-badge-warning",
        "missing": "cp-badge-warning",
        "danger": "cp-badge-danger",
        "error": "cp-badge-danger",
        "rejected": "cp-badge-danger",
        "info": "cp-badge-info",
    }
    cls = kind_map.get(status.lower(), "cp-badge-muted")
    return f'<span class="cp-badge {cls}">{_esc(label)}</span>'


def render_provider_card(name: str, configured: bool, description: str | None = None) -> None:
    badge = render_status_badge("Configured" if configured else "Not Configured", "success" if configured else "warning")
    desc = f'<p class="cp-provider-desc">{_esc(description)}</p>' if description else ""
    st.markdown(
        f"""
        <div class="cp-provider-card">
            <div class="cp-provider-header">
                <span class="cp-provider-name">{_esc(name)}</span>
                {badge}
            </div>
            {desc}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_health_card(name: str, status: str, message: str) -> None:
    kind = {"healthy": "success", "warning": "warning", "error": "danger"}.get(status, "muted")
    badge = render_status_badge(status.title(), kind)
    st.markdown(
        f"""
        <div class="cp-health-card">
            <div class="cp-health-header">
                <span class="cp-health-name">{_esc(name)}</span>
                {badge}
            </div>
            <p class="cp-health-message">{_esc(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(title: str, body: str, icon: str | None = None) -> None:
    icon_html = f'<div class="cp-info-icon">{icon}</div>' if icon else ""
    st.markdown(
        f"""
        <div class="cp-info-card">
            {icon_html}
            <div class="cp-card-title">{_esc(title)}</div>
            <p class="cp-provider-desc">{_esc(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_connector_status(name: str, configured: bool, detail: str = "") -> None:
    """Backward-compatible wrapper around render_provider_card."""
    render_provider_card(name, configured, detail or None)


def render_empty_state(
    title: str,
    subtitle: str = "",
    prompt_placeholder: str | None = None,
    *,
    description: str | None = None,
    icon: str = "✦",
) -> None:
    desc = subtitle or description or ""
    st.markdown(
        f"""
        <div class="cp-welcome-hero">
            <div class="cp-logo-mark">{_esc(icon)}</div>
            <div class="cp-welcome-title">{_esc(title)}</div>
            <div class="cp-welcome-sub">{_esc(desc)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if prompt_placeholder:
        st.caption(prompt_placeholder)


def render_template_card(title: str, description: str = "", icon: str | None = None) -> None:
    icon_html = icon or "📝"
    st.markdown(
        f"""
        <div class="cp-template-card">
            <span style="font-size:1.25rem;">{icon_html}</span>
            <div>
                <div class="cp-card-title">{_esc(title)}</div>
                <p class="cp-provider-desc">{_esc(description)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upgrade_card() -> str:
    return """
    <div class="cp-premium-card">
        <div class="cp-upgrade-title">Premium Plan</div>
        <div class="cp-upgrade-text">Unlock advanced automation, team approval, analytics, and cloud publishing.</div>
    </div>
    """


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            "<div class='cp-sidebar-title'>Artixcore Pilot</div>",
            unsafe_allow_html=True,
        )
        st.caption("ContentPilot")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("+ New", key="sidebar_new", type="primary", use_container_width=True):
                navigate("create_post")
                st.rerun()
        with col_b:
            if st.button("Import", key="sidebar_import", use_container_width=True):
                navigate("ai_workspace")
                st.rerun()

        st.text_input("Search", placeholder="Search...", key="sidebar_search", label_visibility="collapsed")

        selected_label = st.radio(
            "Navigation",
            NAV_LABELS,
            index=NAV_LABELS.index(current_nav_label()) if current_nav_label() in NAV_LABELS else 0,
            label_visibility="collapsed",
            key="nav_radio",
        )
        page_key = key_for_label(selected_label)
        if page_key != st.session_state.nav_page:
            navigate(page_key)
            st.rerun()

        st.markdown("### Works / Projects")
        for ws in SIDEBAR_WORKSPACES:
            if st.button(ws, key=f"ws_{ws}", use_container_width=True):
                st.session_state.active_workspace = ws
                st.rerun()

        st.markdown(render_upgrade_card(), unsafe_allow_html=True)
        if st.button("Upgrade Premium", key="upgrade_btn", type="primary", use_container_width=True):
            st.toast("Premium upgrade coming soon.")


def render_topbar() -> None:
    top_left, top_right = st.columns([1, 1])
    with top_left:
        st.markdown(
            "<div class='cp-topbar-title'>Artixcore ContentPilot</div>",
            unsafe_allow_html=True,
        )
    with top_right:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("Upgrade", key="top_upgrade", use_container_width=True):
                st.toast("Premium upgrade coming soon.")
        with c2:
            st.button("History", key="top_history", use_container_width=True)
        with c3:
            st.button("Alerts", key="top_notify", use_container_width=True)
        with c4:
            if st.button("Profile", key="top_profile", use_container_width=True):
                navigate("brand_settings")
                st.rerun()


def render_alert(message: str, kind: str = "info") -> None:
    st.markdown(
        f'<div class="cp-alert cp-alert-{kind}">{_esc(message)}</div>',
        unsafe_allow_html=True,
    )


def render_platform_badge(platform: str) -> str:
    colors = {
        "linkedin": "#0A66C2",
        "facebook": "#1877F2",
        "instagram": "#E4405F",
        "twitter": "#000000",
        "website_blog": "#D97706",
        "telegram": "#0088CC",
    }
    color = colors.get(platform.lower(), TEXT_SECONDARY)
    plat_label = platform.replace("_", " ").title()
    return (
        f'<span class="cp-badge" style="background:{color}15;color:{color};'
        f'border:1px solid {color}30;">{_esc(plat_label)}</span>'
    )


def render_chat_message(
    role: str,
    content: str,
    provider: str = "",
    show_actions: bool = False,
) -> None:
    if role == "user":
        st.markdown(
            f'<div class="cp-chat-user">{_esc(content).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )
    else:
        meta = ""
        if show_actions or provider:
            actions = "Copy · Like · Dislike · Regenerate" if show_actions else ""
            provider_label = f"Model: {_esc(provider)}" if provider else ""
            meta = f'<div class="cp-chat-meta">{provider_label} {actions}</div>'
        st.markdown(
            f"""
            <div style="display:flex;gap:10px;align-items:flex-start;">
                <div class="cp-logo-mark" style="width:32px;height:32px;font-size:0.75rem;min-width:32px;margin:8px 0 0;">A</div>
                <div class="cp-chat-ai" style="flex:1;margin-left:0;">
                    {_esc(content).replace(chr(10), "<br>")}
                    {meta}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_date_divider(label: str = "TODAY") -> None:
    st.markdown(f'<div class="cp-date-divider">{_esc(label)}</div>', unsafe_allow_html=True)


def render_table_as_cards(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    if not rows:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:0.875rem;">No data to display.</p>',
            unsafe_allow_html=True,
        )
        return
    for row in rows:
        cells = "".join(
            f"""
            <div class="cp-table-card-row">
                <span class="cp-table-card-label">{_esc(label)}</span>
                <span class="cp-table-card-value">{_esc(str(row.get(key, "-")))}</span>
            </div>
            """
            for key, label in columns
        )
        st.markdown(f'<div class="cp-table-card">{cells}</div>', unsafe_allow_html=True)


def render_data_table_or_cards(
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    use_dataframe: bool = True,
) -> None:
    if not rows:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:0.875rem;">No data to display.</p>',
            unsafe_allow_html=True,
        )
        return
    if use_dataframe:
        import pandas as pd

        df = pd.DataFrame([{label: row.get(key, "-") for key, label in columns} for row in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        render_table_as_cards(rows, columns)


def render_two_column_layout(left_ratio: float = 0.65):
    return st.columns([left_ratio, 1 - left_ratio])


def render_welcome_hero() -> None:
    st.markdown(
        """
        <div class="cp-welcome-hero">
            <div class="cp-logo-mark">A</div>
            <div class="cp-welcome-title">Welcome to Artixcore ContentPilot</div>
            <div class="cp-welcome-sub">Your AI content, chatbot, and publishing command center.</div>
            <div class="cp-welcome-sub2">Generate, approve, publish, and learn from every conversation.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_queue_card(
    title: str,
    badges: str,
    preview: str,
    meta: str,
) -> None:
    st.markdown(
        f"""
        <div class="cp-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                <span style="font-weight:600;color:{TEXT_PRIMARY};">{_esc(title)}</span>
                <span>{badges}</span>
            </div>
            <div style="font-size:0.875rem;color:{TEXT_SECONDARY};line-height:1.5;margin-bottom:8px;">
                {_esc(preview[:200])}{"..." if len(preview) > 200 else ""}
            </div>
            <div style="font-size:0.75rem;color:{TEXT_MUTED};">{_esc(meta)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def primary_button(label: str, key: str, disabled: bool = False) -> bool:
    return st.button(label, key=key, type="primary", disabled=disabled, use_container_width=True)


def secondary_button(label: str, key: str) -> bool:
    return st.button(label, key=key, use_container_width=True)

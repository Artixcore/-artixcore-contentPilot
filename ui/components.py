"""Reusable UI components for Artixcore ContentPilot."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ui.navigation import (
    ICON_RAIL,
    SIDEBAR_PRIMARY,
    SIDEBAR_SYSTEM,
    SIDEBAR_WORKSPACES,
    get_current_page_label,
    navigate,
)
from ui.theme import PRIMARY, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY


def _esc(text: str | None) -> str:
    return html.escape(str(text or ""))


def render_page_header(title: str, subtitle: str = "") -> None:
    sub = f'<p class="cp-page-subtitle">{_esc(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<h1 class="cp-page-title">{_esc(title)}</h1>{sub}',
        unsafe_allow_html=True,
    )


def render_section_header(title: str) -> None:
    st.markdown(f'<div class="cp-section-title">{_esc(title)}</div>', unsafe_allow_html=True)


def render_section_title(title: str, subtitle: str | None = None) -> None:
    render_section_header(title)
    if subtitle:
        st.markdown(
            f'<p style="font-size:0.8125rem;color:{TEXT_SECONDARY};margin:-4px 0 12px 0;">{_esc(subtitle)}</p>',
            unsafe_allow_html=True,
        )


def render_card(
    title: str | None = None,
    subtitle: str | None = None,
    body_html: str | None = None,
    class_name: str = "",
    *,
    content_html: str | None = None,
    panel: bool = False,
) -> None:
    """Render a card. Supports legacy content_html/panel kwargs."""
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


def render_metric_card(
    label: str,
    value: str | int,
    icon: str = "",
    status: str | None = None,
) -> str:
    icon_html = f'<div class="cp-metric-icon">{icon}</div>' if icon else ""
    status_html = ""
    if status:
        status_html = f'<div style="margin-top:auto;">{render_status_badge(status)}</div>'
    return f"""
    <div class="cp-metric-card">
        {icon_html}
        <div class="cp-metric-label">{_esc(label)}</div>
        <div class="cp-metric-value">{_esc(str(value))}</div>
        {status_html}
    </div>
    """


def render_metrics_grid(metrics: list[tuple[str, str | int, str]]) -> None:
    """Responsive HTML grid for dashboard metric cards."""
    items = "".join(render_metric_card(label, value, icon) for label, value, icon in metrics)
    n = len(metrics)
    if n <= 5:
        grid_cls = "cp-dashboard-grid"
    else:
        grid_cls = f"cp-grid cp-grid-{min(n, 6)}"
    st.markdown(f'<div class="{grid_cls}">{items}</div>', unsafe_allow_html=True)


def render_metrics_row(metrics: list[tuple[str, str | int, str]]) -> None:
    """Backward-compatible alias — prefers CSS grid."""
    render_metrics_grid(metrics)


def render_status_badge(status: str, kind: str = "muted") -> str:
    kind_map = {
        "success": "cp-badge-success",
        "configured": "cp-badge-success",
        "approved": "cp-badge-success",
        "published": "cp-badge-success",
        "warning": "cp-badge-warning",
        "pending": "cp-badge-warning",
        "missing": "cp-badge-warning",
        "danger": "cp-badge-danger",
        "rejected": "cp-badge-danger",
        "info": "cp-badge-info",
    }
    cls = kind_map.get(kind.lower(), "cp-badge-muted")
    return f'<span class="cp-badge {cls}">{_esc(status)}</span>'


def render_action_button(label: str, key: str, icon: str | None = None, variant: str = "primary") -> bool:
    wrap_cls = "cp-btn-primary" if variant == "primary" else "cp-btn-secondary"
    text = f"{icon} {label}".strip() if icon else label
    st.markdown(f'<div class="{wrap_cls}">', unsafe_allow_html=True)
    clicked = st.button(text, key=key, type="primary" if variant == "primary" else "secondary")
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked


def _nav_button(key: str, label: str, css_class: str = "cp-sidebar-nav") -> None:
    active = st.session_state.nav_page == key
    wrap_cls = f"{css_class}{' active' if active else ''}"
    st.markdown(f'<div class="{wrap_cls}">', unsafe_allow_html=True)
    if st.button(label, key=f"nav_{key}", use_container_width=True):
        navigate(key)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_icon_rail(active_page: str | None = None) -> None:
    page = active_page or st.session_state.nav_page
    st.markdown(
        '<div class="cp-logo-mark" style="width:38px;height:38px;font-size:0.875rem;margin-bottom:8px;">A</div>',
        unsafe_allow_html=True,
    )
    for page_key, icon, tooltip in ICON_RAIL:
        active = page == page_key
        wrap_cls = f"cp-nav-btn-wrap{' active' if active else ''}"
        st.markdown(f'<div class="{wrap_cls}" title="{_esc(tooltip)}">', unsafe_allow_html=True)
        if st.button(icon, key=f"rail_{page_key}", help=tooltip):
            navigate(page_key)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar(active_page: str | None = None) -> None:
    page = active_page or st.session_state.nav_page
    st.markdown(
        f"""
        <div class="cp-sidebar-brand">
            <div class="cp-sidebar-brand-title">Artixcore Pilot</div>
            <div class="cp-sidebar-brand-sub">ContentPilot</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="cp-sidebar-primary-btn">', unsafe_allow_html=True)
        if st.button("+ New Content", key="sidebar_new", type="primary", use_container_width=True):
            navigate("create_post")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="cp-sidebar-secondary-btn">', unsafe_allow_html=True)
        if st.button("Import", key="sidebar_import", use_container_width=True):
            navigate("ai_workspace")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="cp-sidebar-search">', unsafe_allow_html=True)
    st.text_input("Search", placeholder="Search...", key="sidebar_search", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="cp-section-title">Primary</div>', unsafe_allow_html=True)
    for page_key, label in SIDEBAR_PRIMARY:
        _nav_button(page_key, label)

    st.markdown('<div class="cp-section-title">Works / Projects</div>', unsafe_allow_html=True)
    for ws in SIDEBAR_WORKSPACES:
        active = st.session_state.active_workspace == ws
        wrap_cls = f"cp-nav-item cp-workspace-item{' active' if active else ''}"
        st.markdown(f'<div class="{wrap_cls}">', unsafe_allow_html=True)
        if st.button(ws, key=f"ws_{ws}", use_container_width=True):
            st.session_state.active_workspace = ws
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="cp-section-title">System</div>', unsafe_allow_html=True)
    for page_key, label in SIDEBAR_SYSTEM:
        _nav_button(page_key, label)

    st.markdown(render_upgrade_card(), unsafe_allow_html=True)
    st.markdown('<div class="cp-upgrade-card-btn">', unsafe_allow_html=True)
    if st.button("Upgrade Premium", key="upgrade_btn", type="primary", use_container_width=True):
        st.toast("Premium upgrade coming soon.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_topbar(page_title: str | None = None) -> None:
    label = page_title or get_current_page_label()
    st.markdown('<div class="cp-topbar-wrap">', unsafe_allow_html=True)
    left, right = st.columns([2.2, 1.8])
    with left:
        lc1, lc2 = st.columns([0.12, 0.88])
        with lc1:
            st.markdown('<div class="cp-menu-btn">', unsafe_allow_html=True)
            if st.button("☰", key="toggle_sidebar", help="Toggle sidebar"):
                st.session_state.sidebar_open = not st.session_state.sidebar_open
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with lc2:
            st.markdown(f'<div class="cp-topbar-title">{_esc(label)}</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="cp-topbar-actions">', unsafe_allow_html=True)
        ac = st.columns([1.4, 0.55, 0.55, 0.55, 0.55], gap="small")
        with ac[0]:
            st.markdown('<div class="cp-upgrade-btn">', unsafe_allow_html=True)
            if st.button("Upgrade Plan", key="top_upgrade"):
                st.toast("Premium upgrade coming soon.")
            st.markdown("</div>", unsafe_allow_html=True)
        with ac[1]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            st.button("🕐", key="top_history", help="History")
            st.markdown("</div>", unsafe_allow_html=True)
        with ac[2]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            st.button("↗", key="top_share", help="Share")
            st.markdown("</div>", unsafe_allow_html=True)
        with ac[3]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            st.button("🔔", key="top_notify", help="Notifications")
            st.markdown("</div>", unsafe_allow_html=True)
        with ac[4]:
            st.markdown('<div class="cp-icon-btn">', unsafe_allow_html=True)
            if st.button("👤", key="top_profile", help="Profile"):
                navigate("brand_settings")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


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


def render_connector_status(name: str, configured: bool, detail: str = "") -> None:
    badge = render_status_badge("Configured" if configured else "Missing", "success" if configured else "warning")
    detail_html = (
        f'<div style="font-size:0.8125rem;color:{TEXT_SECONDARY};margin-top:4px;">{_esc(detail)}</div>'
        if detail
        else ""
    )
    st.markdown(
        f"""
        <div class="cp-card" style="padding:14px 16px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:600;color:{TEXT_PRIMARY};">{_esc(name)}</span>
                {badge}
            </div>
            {detail_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, description: str = "", icon: str = "✦") -> None:
    st.markdown(
        f"""
        <div class="cp-welcome-hero">
            <div class="cp-logo-mark">{_esc(icon)}</div>
            <div class="cp-welcome-title">{_esc(title)}</div>
            <div class="cp-welcome-sub">{_esc(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_template_card(
    title: str,
    icon: str = "📝",
    action_label: str = "Use",
) -> str:
    return f"""
    <div class="cp-template-card">
        <span style="font-size:1.25rem;">{icon}</span>
        <div class="cp-template-text">{_esc(title)}</div>
        <span class="cp-badge cp-badge-muted">{_esc(action_label)}</span>
    </div>
    """


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


def render_responsive_grid(html_items: list[str], columns: int = 3) -> None:
    grid_cls = f"cp-grid cp-grid-{min(columns, 6)}"
    items = "".join(html_items)
    st.markdown(f'<div class="{grid_cls}">{items}</div>', unsafe_allow_html=True)


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


def render_upgrade_card() -> str:
    return """
    <div class="cp-upgrade-card">
        <div class="cp-upgrade-title">Premium Plan</div>
        <div class="cp-upgrade-text">Unlock advanced automation, team approval, analytics, and cloud publishing.</div>
    </div>
    """


def render_queue_card(
    title: str,
    badges: str,
    preview: str,
    meta: str,
) -> None:
    st.markdown(
        f"""
        <div class="cp-card" style="padding:16px 20px;">
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

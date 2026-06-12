"""Reusable UI components for Artixcore ContentPilot."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

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


def render_card(content_html: str, panel: bool = False) -> None:
    cls = "cp-card-panel" if panel else "cp-card"
    st.markdown(f'<div class="{cls}">{content_html}</div>', unsafe_allow_html=True)


def render_metric_card(label: str, value: str | int, icon: str = "") -> str:
    icon_html = f'<div class="cp-metric-icon">{icon}</div>' if icon else ""
    return f"""
    <div class="cp-metric-card">
        {icon_html}
        <div class="cp-metric-label">{_esc(label)}</div>
        <div class="cp-metric-value">{_esc(str(value))}</div>
    </div>
    """


def render_metrics_row(metrics: list[tuple[str, str | int, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value, icon) in zip(cols, metrics):
        with col:
            st.markdown(render_metric_card(label, value, icon), unsafe_allow_html=True)


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
    label = platform.replace("_", " ").title()
    return (
        f'<span class="cp-badge" style="background:{color}15;color:{color};'
        f'border:1px solid {color}30;">{_esc(label)}</span>'
    )


def render_connector_status(name: str, configured: bool, detail: str = "") -> None:
    badge = render_status_badge("Configured" if configured else "Missing", "success" if configured else "warning")
    detail_html = f'<div style="font-size:0.8125rem;color:{TEXT_SECONDARY};margin-top:4px;">{_esc(detail)}</div>' if detail else ""
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


def render_empty_state(title: str, description: str, icon: str = "✦") -> None:
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


def render_template_card(text: str, icon: str = "📝") -> str:
    return f"""
    <div class="cp-template-card">
        <span style="font-size:1.25rem;">{icon}</span>
        <div class="cp-template-text">{_esc(text)}</div>
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
    """Render table data as stacked cards (mobile-friendly)."""
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
    return f"""
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

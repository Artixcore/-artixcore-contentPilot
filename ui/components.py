"""Backward-compatible UI component wrappers — delegates to bootstrap_components."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.bootstrap_components import (
    alert_html,
    badge,
    chat_message_html,
    date_divider,
    health_card,
    html_escape,
    page_header,
    platform_badge,
    provider_card,
    queue_card,
    section_title,
    template_card,
    welcome_hero,
    widget_section_header,
)
from ui.theme import TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY

_esc = html_escape


def render_page_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(widget_section_header(title, subtitle), unsafe_allow_html=True)


def render_section_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(section_title(title), unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f'<p style="font-size:0.875rem;color:{TEXT_SECONDARY};margin:-8px 0 14px 0;">{_esc(subtitle)}</p>',
            unsafe_allow_html=True,
        )


def render_section_header(title: str) -> None:
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


def render_metric_card(label: str, value: str | int, icon: str = "bi-bar-chart") -> None:
    bi = icon if icon.startswith("bi-") else "bi-bar-chart"
    st.markdown(
        f'<div class="card cp-metric-card border rounded-4 shadow-sm mb-2 p-3">'
        f'<div class="cp-metric-icon"><i class="bi {bi}"></i></div>'
        f'<div class="cp-metric-label">{_esc(label)}</div>'
        f'<div class="cp-metric-value">{_esc(str(value))}</div></div>',
        unsafe_allow_html=True,
    )


def render_status_badge(label: str, status: str = "muted") -> str:
    return badge(label, status)


def render_provider_card(name: str, configured: bool, description: str | None = None) -> None:
    st.markdown(provider_card(name, configured, description or ""), unsafe_allow_html=True)


def render_health_card(name: str, status: str, message: str) -> None:
    st.markdown(health_card(name, status, message), unsafe_allow_html=True)


def render_info_card(title: str, body: str, icon: str | None = None) -> None:
    icon_html = f'<div class="cp-metric-icon"><i class="bi {icon or "bi-info-circle"}"></i></div>' if icon else ""
    st.markdown(
        f'<div class="card border rounded-4 shadow-sm p-3 mb-2">{icon_html}'
        f'<div class="fw-semibold">{_esc(title)}</div>'
        f'<p class="cp-card-subtitle mb-0">{_esc(body)}</p></div>',
        unsafe_allow_html=True,
    )


def render_connector_status(name: str, configured: bool, detail: str = "") -> None:
    render_provider_card(name, configured, detail or None)


def render_empty_state(
    title: str,
    subtitle: str = "",
    prompt_placeholder: str | None = None,
    *,
    description: str | None = None,
    icon: str = "A",
) -> None:
    desc = subtitle or description or ""
    st.markdown(
        f'<div class="cp-welcome-hero text-center">'
        f'<div class="cp-logo-mark">{_esc(icon)}</div>'
        f'<div class="cp-welcome-title">{_esc(title)}</div>'
        f'<div class="cp-welcome-sub">{_esc(desc)}</div></div>',
        unsafe_allow_html=True,
    )
    if prompt_placeholder:
        st.caption(prompt_placeholder)


def render_template_card(title: str, description: str = "", icon: str | None = None) -> None:
    st.markdown(template_card(title, description), unsafe_allow_html=True)


def render_upgrade_card() -> str:
    from ui.bootstrap_components import premium_card
    return premium_card()


def render_alert(message: str, kind: str = "info") -> None:
    st.markdown(alert_html(message, kind), unsafe_allow_html=True)


def render_platform_badge(platform: str) -> str:
    return platform_badge(platform)


def render_chat_message(
    role: str,
    content: str,
    provider: str = "",
    show_actions: bool = False,
) -> None:
    st.markdown(chat_message_html(role, content, provider, show_actions), unsafe_allow_html=True)


def render_date_divider(label: str = "TODAY") -> None:
    st.markdown(date_divider(label), unsafe_allow_html=True)


def render_table_as_cards(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    if not rows:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:0.875rem;">No data to display.</p>',
            unsafe_allow_html=True,
        )
        return
    for row in rows:
        cells = "".join(
            f'<div class="d-flex justify-content-between py-1 border-bottom">'
            f'<span class="text-muted small">{_esc(label)}</span>'
            f'<span class="small fw-medium">{_esc(str(row.get(key, "-")))}</span></div>'
            for key, label in columns
        )
        st.markdown(f'<div class="card border rounded-3 shadow-sm mb-2 p-3">{cells}</div>', unsafe_allow_html=True)


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
    st.markdown(welcome_hero(), unsafe_allow_html=True)


def render_queue_card(
    title: str,
    badges: str,
    preview: str,
    meta: str,
) -> None:
    st.markdown(queue_card(title, badges, preview, meta), unsafe_allow_html=True)


def primary_button(label: str, key: str, disabled: bool = False) -> bool:
    return st.button(label, key=key, type="primary", disabled=disabled, use_container_width=True)


def secondary_button(label: str, key: str) -> bool:
    return st.button(label, key=key, use_container_width=True)

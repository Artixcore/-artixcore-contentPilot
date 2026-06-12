"""User-facing notification helpers."""

from __future__ import annotations

import html

import streamlit as st


def _esc(text: str | None) -> str:
    return html.escape(str(text or ""))


def _render_box(
    title: str,
    kind: str,
    reason: str | None = None,
    action: str | None = None,
    error_code: str | None = None,
) -> None:
    parts = [f'<div class="cp-alert cp-alert-{kind}">']
    parts.append(f'<strong>{_esc(title)}</strong>')
    if reason:
        parts.append(f'<p style="margin:8px 0 0;">{_esc(reason)}</p>')
    if action:
        parts.append(
            f'<p style="margin:8px 0 0;font-size:0.875rem;"><em>Next:</em> {_esc(action)}</p>'
        )
    if error_code:
        parts.append(
            f'<p style="margin:8px 0 0;font-size:0.75rem;opacity:0.7;">Code: {_esc(error_code)}</p>'
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def show_success(message: str) -> None:
    _render_box(message, "success")


def show_error(
    message: str,
    reason: str | None = None,
    action: str | None = None,
    error_code: str | None = None,
) -> None:
    _render_box(message, "error", reason=reason, action=action, error_code=error_code)


def show_warning(
    message: str,
    reason: str | None = None,
    action: str | None = None,
) -> None:
    _render_box(message, "warning", reason=reason, action=action)


def show_info(message: str) -> None:
    _render_box(message, "info")


def show_loading(message: str) -> None:
    st.info(message)


def show_error_from_dict(error_result: dict) -> None:
    """Render error from handle_exception() result dict."""
    show_error(
        message=error_result.get("message", "An error occurred."),
        reason=error_result.get("reason"),
        action=error_result.get("user_action"),
        error_code=error_result.get("error_code"),
    )

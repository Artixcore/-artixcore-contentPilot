"""Loading state helpers for long-running operations."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar

import streamlit as st

from core.safe_runner import safe_execute

T = TypeVar("T")


@contextmanager
def loading_spinner(message: str = "Loading..."):
    with st.spinner(message):
        yield


def loading_overlay(message: str) -> None:
    st.markdown(
        f'<div class="cp-alert cp-alert-info" style="text-align:center;">{_esc(message)}</div>',
        unsafe_allow_html=True,
    )


def _esc(text: str) -> str:
    import html
    return html.escape(text)


def render_skeleton_card() -> None:
    st.markdown(
        """
        <div class="cp-card" style="min-height:120px;opacity:0.6;">
            <div style="background:#E5E7EB;height:16px;width:60%;border-radius:4px;margin-bottom:12px;"></div>
            <div style="background:#E5E7EB;height:12px;width:90%;border-radius:4px;margin-bottom:8px;"></div>
            <div style="background:#E5E7EB;height:12px;width:75%;border-radius:4px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_skeleton_table(rows: int = 5) -> None:
    for _ in range(rows):
        render_skeleton_card()


def render_progress_steps(steps: list[str], current_step: int) -> None:
    html_parts = ['<div style="display:flex;gap:8px;margin:12px 0;">']
    for i, step in enumerate(steps):
        active = i <= current_step
        color = "#D97706" if active else "#E5E7EB"
        text_color = "#fff" if active else "#6B7280"
        html_parts.append(
            f'<div style="flex:1;padding:8px;background:{color};color:{text_color};'
            f'border-radius:6px;font-size:0.75rem;text-align:center;">{_esc(step)}</div>'
        )
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def run_with_loading(
    message: str,
    fn: Callable[..., T],
    *args,
    context: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Run function with spinner and safe execution."""
    with loading_spinner(message):
        return safe_execute(fn, *args, context=context, **kwargs)

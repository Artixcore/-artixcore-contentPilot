"""Streamlit page error boundary."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st
from sqlalchemy.orm import Session

from core.error_handler import handle_exception, log_exception
from ui.notifications import show_error, show_success, show_warning


def render_error_box(error_result: dict) -> None:
    show_error(
        message=error_result.get("message", "Something went wrong."),
        reason=error_result.get("reason"),
        action=error_result.get("user_action"),
        error_code=error_result.get("error_code"),
    )
    if error_result.get("retryable"):
        st.caption("You can retry this action using the button below.")


def render_warning_box(message: str, reason: str | None = None, action: str | None = None) -> None:
    show_warning(message, reason=reason, action=action)


def render_success_box(message: str) -> None:
    show_success(message)


def render_retry_button(label: str = "Retry", key: str | None = None) -> bool:
    return st.button(label, key=key or "error_boundary_retry", type="primary")


def render_database_unavailable_page(error: Exception | None = None) -> None:
    """Show database unavailable page and stop further rendering."""
    from core.errors import DatabaseError

    if isinstance(error, DatabaseError):
        err_dict = error.to_dict()
    elif error:
        err_dict = handle_exception(error, context="database_startup")
    else:
        err_dict = {
            "message": "Database is currently unavailable.",
            "reason": "Could not initialize the local database.",
            "user_action": "Please check local database file permissions or restart the app.",
            "error_code": "DATABASE_ERROR",
        }
    st.error("Database Unavailable")
    render_error_box(err_dict)


def with_error_boundary(page_name: str, render_fn: Callable[[Session], None]):
    """Decorator/wrapper for Streamlit page render functions."""

    def wrapped(session: Session) -> None:
        retry_key = f"retry_{page_name.replace(' ', '_').lower()}"
        try:
            render_fn(session)
        except Exception as exc:
            log_exception(exc, context=f"page:{page_name}")
            error_result = handle_exception(exc, context=f"page:{page_name}")
            st.markdown(f"### {page_name}")
            render_error_box(error_result)
            if render_retry_button("Retry", key=retry_key):
                st.rerun()

    return wrapped

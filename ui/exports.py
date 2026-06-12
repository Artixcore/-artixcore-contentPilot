"""Exports page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.exports import export_csv, export_json, export_markdown, filter_posts
from core.models import PLATFORMS


def render(session: Session) -> None:
    st.title("Exports")
    st.caption("Download posts as CSV, Markdown, or JSON.")

    filter_type = st.selectbox(
        "Filter",
        options=["all", "approved", "pending", "published", "rejected"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    platform = st.selectbox(
        "Platform",
        options=["all"] + list(PLATFORMS),
        format_func=lambda x: "All Platforms" if x == "all" else x.replace("_", " ").title(),
    )
    export_format = st.selectbox("Format", ["CSV", "Markdown", "JSON"])

    posts = filter_posts(session, filter_type=filter_type, platform=platform)
    st.write(f"**{len(posts)}** post(s) match your filters.")

    if not posts:
        st.info("No posts to export with the current filters.")
        return

    try:
        if export_format == "CSV":
            data = export_csv(posts)
            mime = "text/csv"
            filename = "contentpilot_export.csv"
        elif export_format == "Markdown":
            data = export_markdown(posts)
            mime = "text/markdown"
            filename = "contentpilot_export.md"
        else:
            data = export_json(posts)
            mime = "application/json"
            filename = "contentpilot_export.json"

        st.download_button(
            label=f"Download {export_format}",
            data=data,
            file_name=filename,
            mime=mime,
            type="primary",
        )

        with st.expander("Preview"):
            st.text(data[:5000] + ("..." if len(data) > 5000 else ""))

    except Exception as exc:
        from core.utils import format_user_error

        st.error(format_user_error("Export failed. Please try again.", exc))

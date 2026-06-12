"""Exports page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.exports import (
    export_posts_csv,
    export_posts_json,
    export_posts_markdown,
    export_provider_logs_csv,
    export_publishing_logs_csv,
    filter_posts,
)
from core.models import PLATFORMS
from core.training_data import export_training_data_csv, export_training_data_jsonl


EXPORT_TYPES = [
    "Posts — CSV",
    "Posts — JSON",
    "Posts — Markdown",
    "Training Examples — JSONL",
    "Training Examples — CSV",
    "Publishing Logs — CSV",
    "Provider Logs — CSV",
]


def render(session: Session) -> None:
    st.title("Exports")
    st.caption("Download posts, training data, and activity logs.")

    export_type = st.selectbox("Export Type", EXPORT_TYPES)
    include_rejected = False

    posts = []
    if export_type.startswith("Posts"):
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
        posts = filter_posts(session, filter_type=filter_type, platform=platform)
        st.write(f"**{len(posts)}** post(s) match your filters.")
    elif export_type.startswith("Training"):
        include_rejected = st.checkbox("Include rejected examples", value=False)

    try:
        if export_type == "Posts — CSV":
            if not posts:
                st.info("No posts to export.")
                return
            data = export_posts_csv(posts)
            filename, mime = "contentpilot_posts.csv", "text/csv"
        elif export_type == "Posts — JSON":
            if not posts:
                st.info("No posts to export.")
                return
            data = export_posts_json(posts)
            filename, mime = "contentpilot_posts.json", "application/json"
        elif export_type == "Posts — Markdown":
            if not posts:
                st.info("No posts to export.")
                return
            data = export_posts_markdown(posts)
            filename, mime = "contentpilot_posts.md", "text/markdown"
        elif export_type == "Training Examples — JSONL":
            data = export_training_data_jsonl(session, include_rejected=include_rejected)
            filename, mime = "training_data.jsonl", "application/jsonl"
        elif export_type == "Training Examples — CSV":
            data = export_training_data_csv(session, include_rejected=include_rejected)
            filename, mime = "training_data.csv", "text/csv"
        elif export_type == "Publishing Logs — CSV":
            data = export_publishing_logs_csv(session)
            filename, mime = "publishing_logs.csv", "text/csv"
        else:
            data = export_provider_logs_csv(session)
            filename, mime = "provider_logs.csv", "text/csv"

        st.download_button(
            label="Download",
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

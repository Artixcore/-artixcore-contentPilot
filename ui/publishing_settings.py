"""Publishing settings page."""

import os

import streamlit as st
from sqlalchemy.orm import Session

from core.publishing import get_publisher_statuses
from core.utils import mask_secret
from ui.components import render_connector_status, render_page_header, render_section_header

PLATFORM_CONFIG = {
    "linkedin": {
        "label": "LinkedIn",
        "vars": [
            ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_ACCESS_TOKEN"),
            ("LINKEDIN_AUTHOR_URN", "LINKEDIN_AUTHOR_URN"),
            ("LINKEDIN_API_VERSION", "LINKEDIN_API_VERSION"),
        ],
    },
    "twitter": {
        "label": "X / Twitter",
        "vars": [("X_ACCESS_TOKEN", "X_ACCESS_TOKEN")],
    },
    "facebook": {
        "label": "Facebook Page",
        "vars": [
            ("META_PAGE_ID", "META_PAGE_ID"),
            ("META_PAGE_ACCESS_TOKEN", "META_PAGE_ACCESS_TOKEN"),
            ("META_GRAPH_VERSION", "META_GRAPH_VERSION"),
        ],
    },
    "instagram": {
        "label": "Instagram",
        "vars": [
            ("META_IG_USER_ID", "META_IG_USER_ID"),
            ("META_PAGE_ACCESS_TOKEN", "META_PAGE_ACCESS_TOKEN"),
            ("META_GRAPH_VERSION", "META_GRAPH_VERSION"),
        ],
    },
    "website_blog": {
        "label": "Website API",
        "vars": [
            ("WEBSITE_API_BASE_URL", "WEBSITE_API_BASE_URL"),
            ("WEBSITE_API_TOKEN", "WEBSITE_API_TOKEN"),
            ("WEBSITE_POST_ENDPOINT", "WEBSITE_POST_ENDPOINT"),
        ],
    },
}


def render(session: Session) -> None:
    render_page_header("Publishing Settings", "Social platform connector status. Tokens loaded from `.env`.")

    statuses = get_publisher_statuses()

    for platform_key, config in PLATFORM_CONFIG.items():
        configured = statuses.get(platform_key, False)
        with st.container(border=True):
            render_connector_status(config["label"], configured)
            render_section_header("Required Environment Variables")
            for env_name, _ in config["vars"]:
                value = os.getenv(env_name, "")
                if "TOKEN" in env_name or "SECRET" in env_name or "KEY" in env_name:
                    display = mask_secret(value)
                else:
                    display = value or "Not set"
                st.caption(f"`{env_name}`: {display}")

    st.info(
        "OAuth login is not implemented yet. Configure access tokens manually in `.env`. "
        "Production publishing may require platform review and approved permissions."
    )

"""Artixcore ContentPilot — Streamlit application entry point."""

import logging

import streamlit as st
from dotenv import load_dotenv

from core.database import get_session, init_db, seed_default_brand_profile
from ui import approvals, brand_settings, campaigns, create_post, dashboard, exports, provider_settings

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

st.set_page_config(
    page_title="Artixcore ContentPilot",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    [data-testid="stSidebar"] { background-color: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def bootstrap_database():
    init_db()
    session = get_session()
    try:
        seed_default_brand_profile(session)
        session.commit()
    finally:
        session.close()


bootstrap_database()

PAGES = {
    "Dashboard": dashboard.render,
    "Brand Settings": brand_settings.render,
    "Create Post": create_post.render,
    "Approvals": approvals.render,
    "Campaigns": campaigns.render,
    "Provider Settings": provider_settings.render,
    "Exports": exports.render,
}

with st.sidebar:
    st.title("ContentPilot")
    st.caption("Artixcore AI Content Agent")
    st.divider()
    selection = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("MVP v1 — Local-first content workflow")

session = get_session()
try:
    PAGES[selection](session)
except Exception as exc:
    from core.utils import APP_DEBUG, format_user_error

    st.error(format_user_error("Something went wrong loading this page.", exc if APP_DEBUG else None))
finally:
    session.close()

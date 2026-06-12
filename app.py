"""Artixcore ContentPilot — Streamlit application entry point."""

import logging

import streamlit as st
from dotenv import load_dotenv

from core.chat_database import seed_default_chatbot_settings
from core.database import get_session, init_db, seed_default_brand_profile
from ui import (
    approvals,
    brand_settings,
    campaigns,
    chat_control,
    chat_inbox,
    chat_settings,
    create_post,
    dashboard,
    exports,
    provider_settings,
    publish_center,
    publishing_settings,
    training_data,
)

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
        seed_default_chatbot_settings(session)
        session.commit()
    finally:
        session.close()


bootstrap_database()


@st.cache_resource
def start_telegram_controller():
    from chatbot.telegram_controller import start_telegram_polling

    start_telegram_polling()
    return True


start_telegram_controller()

PAGES = {
    "Dashboard": dashboard.render,
    "Brand Settings": brand_settings.render,
    "Create Post": create_post.render,
    "Approvals": approvals.render,
    "Campaigns": campaigns.render,
    "Provider Settings": provider_settings.render,
    "Publishing Settings": publishing_settings.render,
    "Publish Center": publish_center.render,
    "Chat Control": chat_control.render,
    "Chat Inbox": chat_inbox.render,
    "Chat Settings": chat_settings.render,
    "Training Data": training_data.render,
    "Exports": exports.render,
}

with st.sidebar:
    st.title("ContentPilot")
    st.caption("Artixcore AI Content Agent")
    st.divider()
    selection = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("Artixcore ContentPilot — local-first workflow")

session = get_session()
try:
    PAGES[selection](session)
except Exception as exc:
    from core.utils import APP_DEBUG, format_user_error

    st.error(format_user_error("Something went wrong loading this page.", exc if APP_DEBUG else None))
finally:
    session.close()

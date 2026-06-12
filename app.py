"""Artixcore ContentPilot — Streamlit application entry point."""

import logging

import streamlit as st
from dotenv import load_dotenv

from core.chat_database import seed_default_chatbot_settings
from core.database import get_session, init_db, seed_default_brand_profile
from ui.layout import render_app_shell
from ui.theme import load_css, load_js

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

st.set_page_config(
    page_title="Artixcore ContentPilot",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
load_js()


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

session = get_session()
try:
    render_app_shell(session)
except Exception as exc:
    from core.utils import APP_DEBUG, format_user_error

    st.error(format_user_error("Something went wrong loading this page.", exc if APP_DEBUG else None))
finally:
    session.close()

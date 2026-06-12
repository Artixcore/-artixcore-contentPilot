"""Chat Settings page — advanced chatbot configuration."""

import streamlit as st
from sqlalchemy.orm import Session

from core.chat_database import get_blocked_keywords, get_chatbot_settings, update_chatbot_settings
from core.models import CHAT_PLATFORMS
from core.utils import format_user_error


def render(session: Session) -> None:
    st.title("Chat Settings")
    st.caption("Advanced chatbot configuration and safety settings.")

    settings = get_chatbot_settings(session)
    blocked = get_blocked_keywords(settings)
    blocked_text = "\n".join(blocked)

    chatbot_name = st.text_input("Chatbot Name", value=settings.chatbot_name)
    custom_personality = st.text_area(
        "Custom Personality Prompt",
        value=settings.custom_personality_prompt or "",
        help="Used when personality type is Custom Personality.",
    )
    blocked_keywords = st.text_area(
        "Blocked Keywords (one per line)",
        value=blocked_text,
        help="Messages or replies containing these keywords will be flagged.",
    )
    fallback_message = st.text_area(
        "Fallback Message",
        value=settings.fallback_message or "",
    )

    st.subheader("Business Hours")
    business_hours_enabled = st.toggle("Enable Business Hours", value=settings.business_hours_enabled)
    bh1, bh2 = st.columns(2)
    with bh1:
        business_hours_start = st.text_input("Start (HH:MM UTC)", value=settings.business_hours_start or "09:00")
    with bh2:
        business_hours_end = st.text_input("End (HH:MM UTC)", value=settings.business_hours_end or "17:00")

    st.subheader("Platform Notes")
    st.info(
        "**Facebook**: Configure META_PAGE_ID, META_PAGE_ACCESS_TOKEN, META_VERIFY_TOKEN for webhooks.\n\n"
        "**LinkedIn**: Direct messaging API access is restricted. Use manual inbox mode for MVP.\n\n"
        "**X/Twitter**: Reply/DM support depends on your API access tier. Set X_ACCESS_TOKEN."
    )
    for platform in CHAT_PLATFORMS:
        st.caption(f"{platform.title()}: Messages can be simulated from Chat Inbox when API access is limited.")

    if st.button("Save Chat Settings", type="primary"):
        try:
            keywords = [k.strip() for k in blocked_keywords.splitlines() if k.strip()]
            update_chatbot_settings(
                session,
                chatbot_name=chatbot_name,
                custom_personality_prompt=custom_personality or None,
                blocked_keywords=keywords,
                fallback_message=fallback_message or None,
                business_hours_enabled=business_hours_enabled,
                business_hours_start=business_hours_start or None,
                business_hours_end=business_hours_end or None,
            )
            session.commit()
            st.success("Chat settings saved.")
            st.rerun()
        except Exception as exc:
            session.rollback()
            st.error(format_user_error("Failed to save chat settings.", exc))

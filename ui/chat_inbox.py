"""Chat Inbox page — conversations, approvals, and simulation."""

import streamlit as st
from sqlalchemy.orm import Session

from chatbot.chatbot_agent import ArtixcoreChatbotAgent, CHATBOT_PROVIDER_UNAVAILABLE_MSG
from chatbot.channel_router import send_reply
from chatbot.conversation_service import (
    approve_message,
    close_conversation,
    handoff_conversation,
    regenerate_message,
    reject_message_service,
    save_message_feedback,
    simulate_incoming_message,
)
from chatbot.schemas import SimulateMessageRequest
from core.chat_database import get_conversation_messages, list_conversations
from core.models import CHAT_CONVERSATION_STATUSES, CHAT_PLATFORMS
from core.router import ProviderRouter
from core.utils import format_user_error
from ui.components import (
    alert_card,
    badge_html,
    chat_message,
    inbox_item,
    page_header,
    platform_badge,
    section_title,
)


def render_chat_inbox(session: Session) -> None:
    page_header(
        "Chat Inbox",
        "Review conversations, approve AI replies, and simulate incoming messages.",
    )

    router = ProviderRouter(session=session)
    if not router.has_any_provider():
        alert_card(CHATBOT_PROVIDER_UNAVAILABLE_MSG, "error")

    with st.expander("Simulate Incoming Message (local testing)", expanded=False):
        with st.form("simulate_message"):
            sim_platform = st.selectbox("Platform", CHAT_PLATFORMS, key="sim_platform")
            sim_user = st.text_input("User Name", value="Test User")
            sim_message = st.text_area("Message Text", placeholder="Hi, I need a SaaS app built...")
            submitted = st.form_submit_button("Simulate & Generate Reply", type="primary")
            if submitted:
                if not sim_message.strip():
                    st.warning("Message text is required.")
                elif not router.has_any_provider():
                    alert_card(CHATBOT_PROVIDER_UNAVAILABLE_MSG, "error")
                else:
                    try:
                        result = simulate_incoming_message(
                            session,
                            SimulateMessageRequest(
                                platform=sim_platform,
                                user_name=sim_user,
                                message_text=sim_message.strip(),
                            ),
                        )
                        session.commit()
                        if result.success:
                            st.success(f"Draft created (message #{result.message_id}). Status: {result.reply_status}")
                            if result.draft_text:
                                st.text_area("AI Draft Reply", value=result.draft_text, height=150, disabled=True)
                        else:
                            st.error(result.error or "Failed to generate reply.")
                    except Exception as exc:
                        session.rollback()
                        alert_card(format_user_error("Simulation failed.", exc), "error")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        filter_platform = st.selectbox("Platform", ["all"] + list(CHAT_PLATFORMS), key="filter_platform")
    with f2:
        filter_status = st.selectbox("Status", ["all"] + list(CHAT_CONVERSATION_STATUSES), key="filter_status")
    with f3:
        filter_pending = st.checkbox("Pending Approval Only")
    with f4:
        filter_handoff = st.checkbox("Human Handoff Only")

    conversations = list_conversations(
        session,
        platform=filter_platform,
        status=filter_status,
        pending_approval=filter_pending,
        human_handoff=filter_handoff,
    )

    if not conversations:
        st.info("No conversations yet. Use Simulate Incoming Message to create one.")
        return

    if "inbox_selected_id" not in st.session_state:
        st.session_state.inbox_selected_id = conversations[0].id

    list_col, thread_col = st.columns([0.35, 0.65])

    with list_col:
        section_title("Conversations")
        for conv in conversations:
            active = st.session_state.inbox_selected_id == conv.id
            conv_msgs = get_conversation_messages(session, conv.id)
            preview = (
                (conv_msgs[-1].message_text or conv_msgs[-1].ai_generated_reply or "No messages")[:60]
                if conv_msgs
                else "No messages"
            )
            inbox_item(
                conv.user_display_name or "Guest",
                preview,
                conv.status,
                conv.platform,
                active=active,
            )
            if st.button(f"Open #{conv.id}", key=f"open_conv_{conv.id}", use_container_width=True):
                st.session_state.inbox_selected_id = conv.id
                st.rerun()

    selected_id = st.session_state.inbox_selected_id
    conv = next((c for c in conversations if c.id == selected_id), conversations[0])
    messages = get_conversation_messages(session, conv.id)

    with thread_col:
        with st.container(border=True):
            st.markdown(
                f"**{conv.user_display_name or 'Guest'}** · "
                f"{platform_badge(conv.platform)} · "
                f"{badge_html(conv.status, 'info')}",
                unsafe_allow_html=True,
            )

            for msg in messages:
                text = msg.message_text or msg.ai_generated_reply or msg.final_reply or ""
                if msg.sender_type == "user":
                    chat_message("user", text)
                else:
                    chat_message("assistant", text, provider=msg.provider_used or "")

                    if msg.sender_type == "bot" and msg.ai_generated_reply:
                        if msg.safety_notes:
                            st.warning(f"Safety: {msg.safety_notes}")

                        edited = st.text_area(
                            "Final Reply Editor",
                            value=msg.final_reply or msg.ai_generated_reply or "",
                            key=f"edit_{msg.id}",
                        )
                        fb = st.text_input("Human Feedback", value="", key=f"fb_{msg.id}")
                        score = st.slider("Quality Score", 1, 10, 5, key=f"score_{msg.id}")

                        b1, b2, b3, b4 = st.columns(4)
                        with b1:
                            if st.button("Approve & Send", key=f"approve_{msg.id}", type="primary"):
                                msg.final_reply = edited
                                session.flush()
                                ok, message = approve_message(session, msg.id)
                                st.success(message) if ok else st.error(message)
                                st.rerun()
                        with b2:
                            if st.button("Reject", key=f"reject_{msg.id}"):
                                ok, message = reject_message_service(session, msg.id, reason="Rejected from inbox")
                                st.success(message) if ok else st.error(message)
                                st.rerun()
                        with b3:
                            if st.button("Regenerate", key=f"regen_{msg.id}"):
                                if not router.has_any_provider():
                                    alert_card(CHATBOT_PROVIDER_UNAVAILABLE_MSG, "error")
                                else:
                                    result = regenerate_message(session, msg.id)
                                    st.success("Regenerated.") if result.success else st.error(result.error or "Failed")
                                    st.rerun()
                        with b4:
                            if st.button("Save Feedback", key=f"save_fb_{msg.id}"):
                                ok, message = save_message_feedback(session, msg.id, fb or None, score)
                                st.success(message) if ok else st.error(message)
                                st.rerun()

            section_title("Manual Reply")
            manual_text = st.text_area("Manual reply text", key="manual_reply", label_visibility="collapsed")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                if st.button("Send Manual Reply", use_container_width=True):
                    if not manual_text.strip():
                        st.warning("Enter reply text.")
                    else:
                        try:
                            agent = ArtixcoreChatbotAgent(session)
                            msg_id = agent.send_manual_reply(conv.id, conv.platform, manual_text.strip())
                            result = send_reply(session, conv.platform, conv.id, msg_id, manual_text.strip())
                            session.commit()
                            st.success("Manual reply saved.") if result.get("success") else st.warning(
                                f"Saved locally. Platform send: {result.get('error', 'failed')}"
                            )
                            st.rerun()
                        except Exception as exc:
                            session.rollback()
                            alert_card(format_user_error("Manual reply failed.", exc), "error")
            with mc2:
                if st.button("Human Handoff", use_container_width=True):
                    ok, message = handoff_conversation(session, conv.id)
                    st.success(message) if ok else st.error(message)
                    st.rerun()
            with mc3:
                if st.button("Close Conversation", use_container_width=True):
                    ok, message = close_conversation(session, conv.id)
                    st.success(message) if ok else st.error(message)
                    st.rerun()


def render(session: Session) -> None:
    render_chat_inbox(session)

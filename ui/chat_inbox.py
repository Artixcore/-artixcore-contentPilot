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


def render(session: Session) -> None:
    st.title("Chat Inbox")
    st.caption("Review conversations, approve AI replies, and simulate incoming messages.")

    router = ProviderRouter(session=session)
    if not router.has_any_provider():
        st.error(CHATBOT_PROVIDER_UNAVAILABLE_MSG)

    st.subheader("Simulate Incoming Message")
    with st.form("simulate_message"):
        sim_platform = st.selectbox("Platform", CHAT_PLATFORMS, key="sim_platform")
        sim_user = st.text_input("User Name", value="Test User")
        sim_message = st.text_area("Message Text", placeholder="Hi, I need a SaaS app built...")
        submitted = st.form_submit_button("Simulate & Generate Reply", type="primary")
        if submitted:
            if not sim_message.strip():
                st.warning("Message text is required.")
            elif not router.has_any_provider():
                st.error(CHATBOT_PROVIDER_UNAVAILABLE_MSG)
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
                    st.error(format_user_error("Simulation failed.", exc))

    st.divider()
    st.subheader("Conversations")

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

    conv_labels = {
        c.id: f"#{c.id} — {c.platform.title()} — {c.user_display_name or 'Guest'} — {c.status}"
        for c in conversations
    }
    selected_id = st.selectbox("Select Conversation", options=list(conv_labels.keys()), format_func=lambda x: conv_labels[x])

    conv = next(c for c in conversations if c.id == selected_id)
    messages = get_conversation_messages(session, selected_id)

    st.markdown(f"**Status:** {conv.status} | **Platform:** {conv.platform} | **User:** {conv.user_display_name or 'Guest'}")

    for msg in messages:
        role = msg.sender_type.replace("_", " ").title()
        text = msg.message_text or msg.ai_generated_reply or msg.final_reply or ""
        with st.expander(f"{role} — {msg.reply_status} — #{msg.id}"):
            st.write(text)
            if msg.sender_type == "bot" and msg.ai_generated_reply:
                st.caption(f"Provider: {msg.provider_used or 'N/A'} | Model: {msg.model_used or 'N/A'}")
                if msg.safety_notes:
                    st.warning(f"Safety: {msg.safety_notes}")

                edited = st.text_area(
                    "Edit Reply",
                    value=msg.final_reply or msg.ai_generated_reply or "",
                    key=f"edit_{msg.id}",
                )
                fb = st.text_input("Human Feedback", value="", key=f"fb_{msg.id}")
                score = st.slider("Quality Score", 1, 10, 5, key=f"score_{msg.id}")

                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("Approve & Send", key=f"approve_{msg.id}"):
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
                            st.error(CHATBOT_PROVIDER_UNAVAILABLE_MSG)
                        else:
                            result = regenerate_message(session, msg.id)
                            st.success("Regenerated.") if result.success else st.error(result.error or "Failed")
                            st.rerun()
                with b4:
                    if st.button("Save Feedback", key=f"save_fb_{msg.id}"):
                        ok, message = save_message_feedback(session, msg.id, fb or None, score)
                        st.success(message) if ok else st.error(message)
                        st.rerun()

    st.divider()
    st.subheader("Manual Reply")
    manual_text = st.text_area("Manual reply text", key="manual_reply")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        if st.button("Send Manual Reply"):
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
                    st.error(format_user_error("Manual reply failed.", exc))
    with mc2:
        if st.button("Mark Human Handoff"):
            ok, message = handoff_conversation(session, conv.id)
            st.success(message) if ok else st.error(message)
            st.rerun()
    with mc3:
        if st.button("Close Conversation"):
            ok, message = close_conversation(session, conv.id)
            st.success(message) if ok else st.error(message)
            st.rerun()

"""AI Workspace — welcome screen and chat-style agent interface."""

import re

import streamlit as st
from sqlalchemy.orm import Session

from core.agent import AgentValidationError, ContentPilotAgent
from core.router import ProviderRouter
from core.utils import format_user_error
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.components import (
    render_chat_message,
    render_date_divider,
    render_welcome_hero,
)
from ui.navigation import navigate

TEMPLATES = [
    "Create 5 LinkedIn posts for Artixcore SaaS services",
    "Draft replies for new client messages",
    "Generate a weekly social content plan",
    "Prepare chatbot answers for service inquiries",
]

PLATFORM_HINTS = {
    "linkedin": "linkedin",
    "facebook": "facebook",
    "instagram": "instagram",
    "twitter": "twitter",
    "x ": "twitter",
    "blog": "website_blog",
    "website": "website_blog",
}


def _detect_platform(text: str) -> str:
    lower = text.lower()
    for hint, platform in PLATFORM_HINTS.items():
        if hint in lower:
            return platform
    return "linkedin"


def _extract_topic(text: str) -> str:
    cleaned = re.sub(r"^(create|generate|draft|write|prepare)\s+", "", text.strip(), flags=re.I)
    return cleaned[:200] if cleaned else text.strip()


def _add_message(role: str, content: str, provider: str = "") -> None:
    st.session_state.chat_messages.append({"role": role, "content": content, "provider": provider})


def _handle_prompt(session: Session, prompt: str, router: ProviderRouter) -> None:
    _add_message("user", prompt)
    if not router.has_any_provider():
        _add_message("assistant", PROVIDER_UNAVAILABLE_MSG)
        return

    lower = prompt.lower()
    if any(kw in lower for kw in ("chatbot", "reply", "message", "inbox")):
        _add_message(
            "assistant",
            "I can help draft chatbot replies. Open **Chat Inbox** to simulate incoming messages, "
            "approve AI drafts, and send replies to connected platforms.",
            "ContentPilot",
        )
        return

    if any(kw in lower for kw in ("publish", "schedule", "post to")):
        _add_message(
            "assistant",
            "For publishing, approve content in **Approvals** then use **Publish Center** "
            "to send to LinkedIn, Facebook, Instagram, X, or your website.",
            "ContentPilot",
        )
        return

    if any(kw in lower for kw in ("plan", "campaign", "weekly", "content plan")):
        _add_message(
            "assistant",
            "Campaign planning is available in **Campaigns**. I can also generate individual posts — "
            "try asking with a specific topic and platform, e.g. \"Create a LinkedIn post about SaaS MVP development\".",
            "ContentPilot",
        )
        return

    platform = _detect_platform(prompt)
    topic = _extract_topic(prompt)
    with st.spinner("ContentPilot is thinking..."):
        try:
            agent = ContentPilotAgent(session)
            result = agent.generate_post(
                platform=platform,
                topic=topic,
                goal="Engage target audience",
                tone="Professional and approachable",
                language="English",
                cta="",
                provider_mode="auto",
                selected_provider=None,
            )
            tags = " ".join(f"#{h.lstrip('#')}" for h in (result.hashtags or []))
            response = f"{result.content}\n\n"
            if tags:
                response += f"**Hashtags:** {tags}\n\n"
            if result.image_prompt:
                response += f"**Image prompt:** {result.image_prompt}\n\n"
            response += (
                f"Saved as post #{result.post_id} (pending approval). "
                f"Review in Approvals or create more content here."
            )
            _add_message("assistant", response, result.provider_used or "AI")
        except AgentValidationError as exc:
            _add_message("assistant", exc.message)
        except Exception as exc:
            _add_message("assistant", format_user_error("Generation failed. Please try again.", exc))


def render(session: Session) -> None:
    router = ProviderRouter(session=session)
    messages = st.session_state.get("chat_messages", [])

    if not messages:
        render_welcome_hero()
    else:
        render_date_divider("TODAY")
        for msg in messages:
            render_chat_message(
                msg["role"] if msg["role"] == "user" else "assistant",
                msg["content"],
                provider=msg.get("provider", ""),
                show_actions=msg["role"] != "user",
            )

    st.markdown('<div class="cp-chat-input-area">', unsafe_allow_html=True)

    prompt = st.text_area(
        "Prompt",
        placeholder="Ask ContentPilot to create, reply, plan, or publish...",
        key="workspace_prompt",
        label_visibility="collapsed",
        height=80,
    )

    bc1, bc2, bc3, bc4 = st.columns([1, 1, 1, 2])
    with bc1:
        st.button("📎 Attach", key="ws_attach", use_container_width=True)
    with bc2:
        st.button("🖼 Upload Media", key="ws_upload", use_container_width=True)
    with bc3:
        if st.button("Clear Chat", key="ws_clear", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    with bc4:
        send = st.button("Send →", key="ws_send", type="primary", use_container_width=True)

    if send and prompt.strip():
        _handle_prompt(session, prompt.strip(), router)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if not messages:
        st.markdown(
            '<div class="cp-section-title" style="margin-top:24px;">Start with a template</div>',
            unsafe_allow_html=True,
        )
        tc = st.columns(2)
        for i, template in enumerate(TEMPLATES):
            with tc[i % 2]:
                st.markdown(
                    f'<div class="cp-template-card"><span>📝</span>'
                    f'<div class="cp-template-text">{template}</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Use template →", key=f"tpl_{i}", use_container_width=True):
                    _handle_prompt(session, template, router)
                    st.rerun()

    if not router.has_any_provider():
        st.warning(PROVIDER_UNAVAILABLE_MSG)

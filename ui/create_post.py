"""Create post page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.agent import AgentValidationError, ContentPilotAgent
from core.database import get_brand_profile
from core.models import PLATFORMS, Post
from core.router import ProviderRouter
from ui.notifications import show_error_from_dict, show_success
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.components import (
    render_alert,
    render_connector_status,
    render_page_header,
    render_section_header,
    render_status_badge,
)

PLATFORM_LABELS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "twitter": "X / Twitter",
    "website_blog": "Website Blog",
}

PLATFORM_ICONS = {
    "facebook": "📘",
    "instagram": "📷",
    "linkedin": "💼",
    "twitter": "🐦",
    "website_blog": "🌐",
}

PROVIDER_MODES = ["auto", "manual", "fallback", "quality"]
PROVIDERS = ["openai", "anthropic"]


def render(session: Session) -> None:
    render_page_header("Create Post", "Generate AI-powered content for your selected platform.")

    router = ProviderRouter(session=session)
    if not router.has_any_provider():
        render_alert(PROVIDER_UNAVAILABLE_MSG, "error")

    brand = get_brand_profile(session)
    default_tone = brand.tone if brand else ""
    default_cta = brand.preferred_cta if brand else ""
    availability = router.get_availability_status()

    if "create_platform" not in st.session_state:
        st.session_state.create_platform = "linkedin"

    render_section_header("Select Platform")
    pcols = st.columns(len(PLATFORMS))
    for col, plat in zip(pcols, PLATFORMS):
        with col:
            selected = st.session_state.create_platform == plat
            style = "border-color:#D97706;background:#FFF7ED;" if selected else ""
            st.markdown(
                f'<div class="cp-platform-card" style="{style}">'
                f'<div style="font-size:1.5rem;">{PLATFORM_ICONS.get(plat, "📄")}</div>'
                f'<div style="font-weight:600;margin-top:8px;">{PLATFORM_LABELS.get(plat, plat)}</div></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Select {PLATFORM_LABELS.get(plat, plat)}", key=f"plat_{plat}", use_container_width=True):
                st.session_state.create_platform = plat
                st.rerun()

    platform = st.session_state.create_platform
    main_col, side_col = st.columns([0.65, 0.35])

    with main_col:
        topic = st.text_input("Topic *", placeholder="e.g. Building a SaaS MVP in 90 days")
        goal = st.text_input("Goal", placeholder="e.g. Drive consultation bookings")
        c1, c2 = st.columns(2)
        with c1:
            tone = st.text_input("Tone", value=default_tone)
            language = st.selectbox("Language", ["English", "Arabic", "French", "Spanish", "German"])
        with c2:
            cta = st.text_input("CTA", value=default_cta)
            provider_mode = st.selectbox("Provider Mode", PROVIDER_MODES)
        selected_provider = st.selectbox(
            "Selected Provider",
            PROVIDERS,
            index=0,
            help="Used in manual and fallback modes.",
        )

        generate = st.button("Generate Post", type="primary", disabled=not router.has_any_provider())

    with side_col:
        with st.container(border=True):
            render_section_header("Brand Profile")
            if brand:
                st.markdown(
                    f"**{brand.company_name or 'Artixcore'}**  \n"
                    f"{brand.description[:120] + '...' if brand.description and len(brand.description) > 120 else brand.description or ''}"
                )
            render_section_header("Provider Status")
            render_connector_status("OpenAI", bool(availability.get("openai")))
            render_connector_status("Anthropic", bool(availability.get("anthropic")))
            st.caption("All generated content requires human approval before publishing.")
            render_section_header("Similar Posts")
            similar = (
                session.query(Post)
                .filter(Post.platform == platform)
                .order_by(Post.created_at.desc())
                .limit(3)
                .all()
            )
            if similar:
                for p in similar:
                    st.caption(f"#{p.id} — {p.topic[:40]}")
            else:
                st.caption("No similar posts yet.")

    if generate:
        if not topic or not topic.strip():
            render_alert("Topic is required. Please enter a topic for your post.", "error")
            return

        from core.safe_runner import safe_streamlit_action
        from ui.loading import loading_spinner

        agent = ContentPilotAgent(session)
        with loading_spinner("Generating with AI provider..."):
            outcome = safe_streamlit_action(
                "generate_post",
                agent.generate_post,
                platform=platform,
                topic=topic.strip(),
                goal=goal or "",
                tone=tone or "",
                language=language,
                cta=cta or "",
                provider_mode=provider_mode,
                selected_provider=selected_provider if provider_mode in ("manual", "fallback") else None,
                load_type="ai",
            )
        if not outcome.get("success"):
            show_error_from_dict(outcome.get("error") or {})
            return
        result = outcome.get("result")
        if result:
            show_success(f"Post saved (ID: {result.post_id}) — pending approval")

            with st.container(border=True):
                render_section_header("Generated Content Preview")
                st.text_area("Content", value=result.content, height=200, disabled=True, label_visibility="collapsed")

                if result.hashtags:
                    tags = " ".join(f"#{h.lstrip('#')}" for h in result.hashtags)
                    st.write(f"**Hashtags:** {tags}")

                if result.image_prompt:
                    st.write(f"**Image Prompt:** {result.image_prompt}")

                mc1, mc2, mc3 = st.columns(3)
                mc1.write(f"**Provider:** {result.provider_used}")
                mc2.write(f"**Model:** {result.model_used or 'N/A'}")
                mc3.markdown(render_status_badge("Pending Approval", "pending"), unsafe_allow_html=True)

                if result.quality_notes:
                    render_alert(f"Quality Notes: {result.quality_notes}", "info")

                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    st.button("Save", key="gen_save", disabled=True, use_container_width=True)
                with bc2:
                    if st.button("Go to Approvals", key="gen_approve", use_container_width=True):
                        from ui.navigation import navigate
                        navigate("approvals")
                        st.rerun()
                with bc3:
                    st.button("Edit", key="gen_edit", use_container_width=True)

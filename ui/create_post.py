"""Create post page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.agent import AgentValidationError, ContentPilotAgent
from core.database import get_brand_profile
from core.models import PLATFORMS, Post
from core.router import ProviderRouter
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.components import alert_card, badge_html, page_header, section_title, status_card
from ui.loading import loading_spinner
from ui.navigation import navigate
from ui.notifications import show_error_from_dict, show_success

PLATFORM_LABELS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "twitter": "X / Twitter",
    "website_blog": "Website Blog",
}

PROVIDER_MODES = ["auto", "manual", "fallback", "quality"]
PROVIDERS = ["openai", "anthropic"]


def render_create_post(session: Session) -> None:
    router = ProviderRouter(session=session)
    page_header("Create Post", "Generate AI-powered content for your selected platform.")

    if not router.has_any_provider():
        alert_card(PROVIDER_UNAVAILABLE_MSG, "error")

    brand = get_brand_profile(session)
    default_tone = brand.tone if brand else ""
    default_cta = brand.preferred_cta if brand else ""
    availability = router.get_availability_status()

    section_title("Select Platform")
    platform = st.selectbox(
        "Platform",
        PLATFORMS,
        format_func=lambda x: PLATFORM_LABELS.get(x, x),
        key="create_platform_select",
    )

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
            section_title("Brand Profile")
            if brand:
                st.markdown(
                    f"**{brand.company_name or 'Artixcore'}**  \n"
                    f"{brand.description[:120] + '...' if brand.description and len(brand.description) > 120 else brand.description or ''}"
                )
            section_title("Provider Status")
            for name, ok in [("OpenAI", availability.get("openai")), ("Anthropic", availability.get("anthropic"))]:
                status_card(
                    name,
                    "Configured." if ok else "API key missing.",
                    "success" if ok else "warning",
                )
            st.caption("All generated content requires human approval before publishing.")
            section_title("Similar Posts")
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
            alert_card("Topic is required. Please enter a topic for your post.", "error")
            return

        from core.safe_runner import safe_streamlit_action

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
                section_title("Generated Content Preview")
                st.text_area("Content", value=result.content, height=200, disabled=True, label_visibility="collapsed")

                if result.hashtags:
                    tags = " ".join(f"#{h.lstrip('#')}" for h in result.hashtags)
                    st.write(f"**Hashtags:** {tags}")

                if result.image_prompt:
                    st.write(f"**Image Prompt:** {result.image_prompt}")

                mc1, mc2, mc3 = st.columns(3)
                mc1.write(f"**Provider:** {result.provider_used}")
                mc2.write(f"**Model:** {result.model_used or 'N/A'}")
                mc3.markdown(badge_html("Pending Approval", "pending"), unsafe_allow_html=True)

                if result.quality_notes:
                    alert_card(f"Quality Notes: {result.quality_notes}", "info")

                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    st.button("Save", key="gen_save", disabled=True, use_container_width=True)
                with bc2:
                    if st.button("Go to Approvals", key="gen_approve", use_container_width=True):
                        navigate("Approvals")
                with bc3:
                    st.button("Edit", key="gen_edit", use_container_width=True)


def render(session: Session) -> None:
    render_create_post(session)

"""Create post page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.agent import AgentValidationError, ContentPilotAgent
from core.database import get_brand_profile
from core.models import PLATFORMS
from core.router import ProviderRouter
from core.utils import format_user_error
from providers import PROVIDER_UNAVAILABLE_MSG


PLATFORM_LABELS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "twitter": "Twitter/X",
    "website_blog": "Website Blog",
}

PROVIDER_MODES = ["auto", "manual", "fallback", "quality"]
PROVIDERS = ["openai", "anthropic"]


def render(session: Session) -> None:
    st.title("Create Post")
    st.caption("Generate AI-powered content for your selected platform.")

    router = ProviderRouter(session=session)
    if not router.has_any_provider():
        st.error(PROVIDER_UNAVAILABLE_MSG)

    brand = get_brand_profile(session)
    default_tone = brand.tone if brand else ""
    default_cta = brand.preferred_cta if brand else ""

    col1, col2 = st.columns(2)
    with col1:
        platform = st.selectbox(
            "Platform",
            options=list(PLATFORMS),
            format_func=lambda x: PLATFORM_LABELS.get(x, x),
        )
        topic = st.text_input("Topic *", placeholder="e.g. Building a SaaS MVP in 90 days")
        goal = st.text_input("Goal", placeholder="e.g. Drive consultation bookings")
        tone = st.text_input("Tone", value=default_tone)
    with col2:
        language = st.selectbox("Language", ["English", "Arabic", "French", "Spanish", "German"])
        cta = st.text_input("CTA", value=default_cta)
        provider_mode = st.selectbox("Provider Mode", PROVIDER_MODES)
        selected_provider = st.selectbox(
            "Selected Provider",
            PROVIDERS,
            index=0,
            help="Used in manual and fallback modes.",
        )

    generate = st.button("Generate Post", type="primary", disabled=not router.has_any_provider())

    if generate:
        if not topic or not topic.strip():
            st.error("Topic is required. Please enter a topic for your post.")
            return

        with st.spinner("Generating content..."):
            try:
                agent = ContentPilotAgent(session)
                result = agent.generate_post(
                    platform=platform,
                    topic=topic.strip(),
                    goal=goal or "",
                    tone=tone or "",
                    language=language,
                    cta=cta or "",
                    provider_mode=provider_mode,
                    selected_provider=selected_provider if provider_mode in ("manual", "fallback") else None,
                )
                st.success(f"Post saved to database (ID: {result.post_id}) — status: pending_approval")

                st.subheader("Generated Content")
                st.text_area("Content", value=result.content, height=200, disabled=True)

                if result.hashtags:
                    tags = " ".join(f"#{h.lstrip('#')}" for h in result.hashtags)
                    st.write(f"**Hashtags:** {tags}")

                if result.image_prompt:
                    st.write(f"**Image Prompt:** {result.image_prompt}")

                c1, c2 = st.columns(2)
                c1.write(f"**Provider:** {result.provider_used}")
                c2.write(f"**Model:** {result.model_used or 'N/A'}")

                if result.quality_notes:
                    st.info(f"**Quality Notes:** {result.quality_notes}")

            except AgentValidationError as exc:
                st.error(exc.message)
            except Exception as exc:
                st.error(format_user_error("Content generation failed. Please try again.", exc))

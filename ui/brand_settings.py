"""Brand settings page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.database import get_brand_profile
from core.schemas import BrandProfileUpdate
from ui.components import page_header, section_title
from ui.notifications import show_error_from_dict, show_success


def render_brand_settings(session: Session) -> None:
    page_header(
        "Brand Settings",
        "Configure the Artixcore brand profile used for content generation.",
    )

    profile = get_brand_profile(session)
    if not profile:
        st.error("Brand profile not found. The default profile will be created on next app restart.")
        return

    with st.container(border=True):
        with st.form("brand_form"):
            section_title("Company Profile")
            c1, c2 = st.columns(2)
            with c1:
                company_name = st.text_input("Company Name", value=profile.company_name)
                page_name = st.text_input("Page Name", value=profile.page_name)
                website_url = st.text_input("Website URL", value=profile.website_url)
            with c2:
                description = st.text_area("Description", value=profile.description, height=100)
                tone = st.text_area("Tone", value=profile.tone, height=80)

            section_title("Audience & Style")
            target_audience = st.text_area("Target Audience", value=profile.target_audience, height=80)
            services = st.text_area("Services", value=profile.services, height=80)
            preferred_cta = st.text_area("Preferred CTA", value=profile.preferred_cta, height=80)
            forbidden_style = st.text_area("Forbidden Style", value=profile.forbidden_style, height=80)

            submitted = st.form_submit_button("Save Brand Profile", type="primary", use_container_width=True)

    if submitted:
        from core.cache import invalidate_prefix
        from core.safe_runner import safe_streamlit_action

        def _save_brand():
            data = BrandProfileUpdate(
                company_name=company_name,
                page_name=page_name,
                website_url=website_url,
                description=description,
                tone=tone,
                target_audience=target_audience,
                services=services,
                preferred_cta=preferred_cta,
                forbidden_style=forbidden_style,
            )
            profile.company_name = data.company_name
            profile.page_name = data.page_name
            profile.website_url = data.website_url
            profile.description = data.description
            profile.tone = data.tone
            profile.target_audience = data.target_audience
            profile.services = data.services
            profile.preferred_cta = data.preferred_cta
            profile.forbidden_style = data.forbidden_style
            session.commit()
            invalidate_prefix("brand_profile")
            invalidate_prefix("settings")
            return True

        outcome = safe_streamlit_action("save_settings", _save_brand)
        if outcome.get("success"):
            show_success("Brand profile saved successfully.")
        else:
            session.rollback()
            show_error_from_dict(outcome.get("error") or {})


def render(session: Session) -> None:
    render_brand_settings(session)

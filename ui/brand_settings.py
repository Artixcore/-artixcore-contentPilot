"""Brand settings page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.database import get_brand_profile
from core.schemas import BrandProfileUpdate
from ui.components import render_page_header, render_section_header


def render(session: Session) -> None:
    render_page_header("Brand Settings", "Configure the Artixcore brand profile used for content generation.")

    profile = get_brand_profile(session)
    if not profile:
        st.error("Brand profile not found. The default profile will be created on next app restart.")
        return

    st.markdown('<div class="cp-card">', unsafe_allow_html=True)
    with st.form("brand_form"):
        render_section_header("Company Profile")
        c1, c2 = st.columns(2)
        with c1:
            company_name = st.text_input("Company Name", value=profile.company_name)
            page_name = st.text_input("Page Name", value=profile.page_name)
            website_url = st.text_input("Website URL", value=profile.website_url)
        with c2:
            description = st.text_area("Description", value=profile.description, height=100)
            tone = st.text_area("Tone", value=profile.tone, height=80)

        render_section_header("Audience & Style")
        target_audience = st.text_area("Target Audience", value=profile.target_audience, height=80)
        services = st.text_area("Services", value=profile.services, height=80)
        preferred_cta = st.text_area("Preferred CTA", value=profile.preferred_cta, height=80)
        forbidden_style = st.text_area("Forbidden Style", value=profile.forbidden_style, height=80)

        submitted = st.form_submit_button("Save Brand Profile", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        try:
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
            st.success("Brand profile saved successfully.")
        except Exception as exc:
            session.rollback()
            from core.utils import format_user_error

            st.error(format_user_error("Failed to save brand profile. Check your inputs.", exc))

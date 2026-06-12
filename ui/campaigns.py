"""Campaigns page."""

from datetime import datetime

import streamlit as st
from sqlalchemy.orm import Session

from core.agent import AgentValidationError, ContentPilotAgent
from core.models import PLATFORMS, Campaign
from core.utils import platforms_from_json, platforms_to_json
from ui.bootstrap_components import badge, section_title, widget_section_header


def render(session: Session) -> None:
    st.markdown(
        widget_section_header("Campaigns", "Plan and manage content campaigns."),
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(section_title("Create Campaign"), unsafe_allow_html=True)
        with st.form("campaign_form"):
            name = st.text_input("Campaign Name *")
            goal = st.text_input("Goal")
            description = st.text_area("Description", height=100)
            platforms = st.multiselect(
                "Platforms",
                options=list(PLATFORMS),
                default=["linkedin", "facebook"],
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                start_date = st.date_input("Start Date")
            with c2:
                end_date = st.date_input("End Date")
            with c3:
                posts_per_week = st.number_input("Posts Per Week", min_value=1, max_value=50, value=3)

            submitted = st.form_submit_button("Save Campaign", type="primary", use_container_width=True)

    if submitted:
        if not name or not name.strip():
            st.error("Campaign name is required.")
        else:
            try:
                campaign = Campaign(
                    name=name.strip(),
                    goal=goal or "",
                    description=description or "",
                    platforms=platforms_to_json(platforms),
                    start_date=datetime.combine(start_date, datetime.min.time()) if start_date else None,
                    end_date=datetime.combine(end_date, datetime.min.time()) if end_date else None,
                    posts_per_week=int(posts_per_week),
                    status="active",
                )
                session.add(campaign)
                session.commit()
                st.success(f"Campaign '{campaign.name}' saved.")
                st.rerun()
            except Exception as exc:
                session.rollback()
                st.error(f"Failed to save campaign: {type(exc).__name__}")

    st.markdown(section_title("Your Campaigns"), unsafe_allow_html=True)
    campaigns = session.query(Campaign).order_by(Campaign.created_at.desc()).all()

    if not campaigns:
        st.info("No campaigns yet.")
        return

    for campaign in campaigns:
        status_badge = badge(campaign.status or "active", "info")
        st.markdown(
            f'<div class="cp-card"><div style="display:flex;justify-content:space-between;">'
            f'<strong>{campaign.name}</strong> {status_badge}</div></div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"Details — {campaign.name}"):
            st.write(f"**Goal:** {campaign.goal or 'N/A'}")
            st.write(f"**Description:** {campaign.description or 'N/A'}")
            plats = platforms_from_json(campaign.platforms)
            st.write(f"**Platforms:** {', '.join(plats) if plats else 'None'}")
            st.write(f"**Posts/week:** {campaign.posts_per_week}")
            if campaign.start_date:
                st.write(f"**Start:** {campaign.start_date.date()}")
            if campaign.end_date:
                st.write(f"**End:** {campaign.end_date.date()}")

            if st.button("Generate Post Ideas", key=f"ideas_{campaign.id}", type="primary"):
                with st.spinner("Generating campaign ideas..."):
                    try:
                        agent = ContentPilotAgent(session)
                        ideas = agent.generate_campaign_ideas(campaign.id)
                        st.success(f"Ideas generated via {ideas.provider_used}")
                        st.write("**Campaign Angles:**")
                        for idea in ideas.ideas:
                            st.write(f"- {idea}")
                        st.write("**Post Topics:**")
                        for topic in ideas.topics:
                            st.write(f"- {topic}")
                    except AgentValidationError as exc:
                        st.error(exc.message)
                    except Exception as exc:
                        st.error(f"Failed to generate ideas: {type(exc).__name__}")

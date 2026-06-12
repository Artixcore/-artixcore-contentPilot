"""Dashboard page."""

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from core.models import Post
from core.router import ProviderRouter
from providers import PROVIDER_UNAVAILABLE_MSG


def render(session: Session) -> None:
    st.title("Dashboard")
    st.caption("Overview of your content pipeline and provider status.")

    total = session.query(Post).count()
    pending = session.query(Post).filter(Post.status == "pending_approval").count()
    approved = session.query(Post).filter(Post.status == "approved").count()
    rejected = session.query(Post).filter(Post.status == "rejected").count()
    published = session.query(Post).filter(Post.status == "published").count()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Posts", total)
    c2.metric("Pending Approval", pending)
    c3.metric("Approved", approved)
    c4.metric("Rejected", rejected)
    c5.metric("Published", published)

    st.divider()
    st.subheader("Provider Availability")
    router = ProviderRouter(session=session)
    availability = router.get_availability_status()

    if not availability.get("openai") and not availability.get("anthropic"):
        st.error(PROVIDER_UNAVAILABLE_MSG)

    p1, p2 = st.columns(2)
    with p1:
        status = "Available" if availability.get("openai") else "Missing API Key"
        st.info(f"**OpenAI:** {status}")
    with p2:
        status = "Available" if availability.get("anthropic") else "Missing API Key"
        st.info(f"**Anthropic:** {status}")

    st.divider()
    st.subheader("Recent Posts")
    posts = session.query(Post).order_by(Post.created_at.desc()).limit(20).all()
    if posts:
        rows = [
            {
                "ID": p.id,
                "Platform": p.platform,
                "Topic": p.topic[:50],
                "Status": p.status,
                "Provider": p.provider_used or "-",
                "Created": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            }
            for p in posts
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.write("No posts yet. Create your first post from the Create Post page.")

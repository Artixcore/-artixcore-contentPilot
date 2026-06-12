"""Publish Center — manual publishing for approved posts."""

import streamlit as st
from sqlalchemy.orm import Session

from core.models import PLATFORMS
from core.publishing import PublishError, get_publishable_posts, get_publisher_statuses, mark_as_manually_posted, publish_post
from core.utils import format_user_error
from ui.components import (
    render_connector_status,
    render_page_header,
    render_platform_badge,
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


def render(session: Session) -> None:
    render_page_header("Publish Center", "Publish approved or scheduled posts. Human confirmation required.")

    pub_statuses = get_publisher_statuses()
    main_col, side_col = st.columns([0.7, 0.3])

    with side_col:
        st.markdown('<div class="cp-card-panel">', unsafe_allow_html=True)
        render_section_header("Connector Status")
        for key, label in PLATFORM_LABELS.items():
            render_connector_status(label, pub_statuses.get(key, False))
        st.markdown("</div>", unsafe_allow_html=True)

    with main_col:
        posts = get_publishable_posts(session)
        if not posts:
            st.info("No approved or scheduled posts ready to publish.")
            return

        st.markdown(f"**{len(posts)}** post(s) ready to publish.")

        for post in posts:
            st.markdown('<div class="cp-card">', unsafe_allow_html=True)
            header = (
                f"#{post.id} — {post.topic[:60]} "
                f"{render_platform_badge(post.platform)} "
                f"{render_status_badge(post.status.replace('_', ' ').title(), 'approved')}"
            )
            st.markdown(header, unsafe_allow_html=True)
            st.caption(
                f"Provider: {post.provider_used or 'N/A'} · "
                f"Created: {post.created_at.strftime('%Y-%m-%d %H:%M') if post.created_at else 'N/A'}"
            )
            st.text_area(
                "Content Preview",
                value=post.content[:500],
                height=120,
                disabled=True,
                key=f"preview_{post.id}",
                label_visibility="collapsed",
            )

            target_platform = st.selectbox(
                "Target publish platform",
                options=list(PLATFORMS),
                format_func=lambda x: PLATFORM_LABELS.get(x, x),
                key=f"platform_{post.id}",
            )

            image_url = ""
            if target_platform == "instagram":
                image_url = st.text_input(
                    "Public Image URL (required for Instagram)",
                    key=f"image_{post.id}",
                    placeholder="https://example.com/image.jpg",
                )

            confirmed = st.checkbox(
                "I confirm this content is approved and ready to publish",
                key=f"confirm_{post.id}",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Publish",
                    key=f"publish_{post.id}",
                    type="primary",
                    disabled=not confirmed,
                    use_container_width=True,
                ):
                    try:
                        with st.spinner("Publishing..."):
                            result = publish_post(
                                session,
                                post.id,
                                target_platform,
                                image_url=image_url if target_platform == "instagram" else None,
                            )
                        if result.get("success"):
                            st.success(
                                f"Published! ID: {result.get('external_post_id', 'N/A')}"
                            )
                            if result.get("external_post_url"):
                                st.write(f"URL: {result['external_post_url']}")
                            st.rerun()
                        else:
                            st.error(result.get("error", "Publish failed."))
                    except PublishError as exc:
                        st.error(exc.message)
                    except Exception as exc:
                        st.error(format_user_error("Publish failed.", exc))

            with col2:
                if st.button("Mark Manually Posted", key=f"manual_{post.id}", use_container_width=True):
                    ok, msg = mark_as_manually_posted(session, post.id, target_platform)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            if post.publish_error:
                st.warning(f"Last publish error: {post.publish_error}")
            st.markdown("</div>", unsafe_allow_html=True)

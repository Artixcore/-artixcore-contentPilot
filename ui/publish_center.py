"""Publish Center — manual publishing for approved posts."""

import streamlit as st
from sqlalchemy.orm import Session

from core.models import PLATFORMS
from core.publishing import get_publishable_posts, get_publisher_statuses, mark_as_manually_posted, publish_post
from ui.components import badge_html, connector_row, page_header, platform_badge, section_title
from ui.loading import loading_spinner
from ui.notifications import show_error_from_dict, show_success

PLATFORM_LABELS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "twitter": "X / Twitter",
    "website_blog": "Website Blog",
}


def render_publish_center(session: Session) -> None:
    page_header(
        "Publish Center",
        "Publish approved or scheduled posts. Human confirmation required.",
    )

    pub_statuses = get_publisher_statuses()
    main_col, side_col = st.columns([0.7, 0.3])

    with side_col:
        with st.container(border=True):
            section_title("Connector Status")
            for key, label in PLATFORM_LABELS.items():
                connector_row(label, pub_statuses.get(key, False))

    with main_col:
        posts = get_publishable_posts(session)
        if not posts:
            st.info("No approved or scheduled posts ready to publish.")
            return

        st.markdown(f"**{len(posts)}** post(s) ready to publish.")

        for post in posts:
            with st.container(border=True):
                st.markdown(
                    f"#{post.id} — {post.topic[:60]} "
                    f"{platform_badge(post.platform)} "
                    f"{badge_html(post.status.replace('_', ' ').title(), 'approved')}",
                    unsafe_allow_html=True,
                )
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
                        from core.safe_runner import safe_streamlit_action

                        with loading_spinner(f"Publishing to {target_platform.replace('_', ' ').title()}..."):
                            outcome = safe_streamlit_action(
                                "publish_post",
                                publish_post,
                                session,
                                post.id,
                                target_platform,
                                image_url=image_url if target_platform == "instagram" else None,
                                load_type="publish",
                            )
                        if not outcome.get("success"):
                            show_error_from_dict(outcome.get("error") or {})
                        else:
                            result = outcome.get("result") or {}
                            if result.get("success"):
                                show_success(f"Published! ID: {result.get('external_post_id', 'N/A')}")
                                if result.get("external_post_url"):
                                    st.write(f"URL: {result['external_post_url']}")
                                st.rerun()
                            else:
                                show_error_from_dict({
                                    "message": "Publish failed.",
                                    "reason": result.get("error", "Unknown error"),
                                    "user_action": "Check publishing settings and try again.",
                                    "error_code": "PUBLISHING_ERROR",
                                })

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


def render(session: Session) -> None:
    render_publish_center(session)

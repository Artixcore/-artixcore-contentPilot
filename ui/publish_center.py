"""Publish Center — manual publishing for approved posts."""

import streamlit as st
from sqlalchemy.orm import Session

from core.models import PLATFORMS
from core.publishing import PublishError, get_publishable_posts, mark_as_manually_posted, publish_post
from core.utils import format_user_error

PLATFORM_LABELS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "twitter": "Twitter/X",
    "website_blog": "Website Blog",
}


def render(session: Session) -> None:
    st.title("Publish Center")
    st.caption("Publish approved or scheduled posts. Human confirmation required — no auto-publishing.")

    posts = get_publishable_posts(session)
    if not posts:
        st.info("No approved or scheduled posts ready to publish.")
        return

    st.write(f"**{len(posts)}** post(s) ready to publish.")

    for post in posts:
        with st.expander(f"#{post.id} — {post.platform.title()} — {post.topic[:60]}"):
            st.write(f"**Status:** {post.status}")
            st.write(f"**Provider:** {post.provider_used or 'N/A'} | **Model:** {post.model_used or 'N/A'}")
            st.write(f"**Created:** {post.created_at.strftime('%Y-%m-%d %H:%M') if post.created_at else 'N/A'}")
            st.text_area("Content Preview", value=post.content[:500], height=120, disabled=True, key=f"preview_{post.id}")

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
                                f"Published successfully! "
                                f"ID: {result.get('external_post_id', 'N/A')}"
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
                if st.button("Mark as Manually Posted", key=f"manual_{post.id}"):
                    ok, msg = mark_as_manually_posted(session, post.id, target_platform)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            if post.publish_error:
                st.warning(f"Last publish error: {post.publish_error}")

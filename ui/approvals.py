"""Approvals page."""

from datetime import datetime

import streamlit as st
from sqlalchemy.orm import Session

from core.agent import ContentPilotAgent
from core.approvals import (
    approve_post,
    get_pending_posts,
    mark_published,
    regenerate_post,
    reject_post,
    schedule_post,
    update_content,
)
from core.utils import format_user_error, hashtags_from_json


def render(session: Session) -> None:
    st.title("Approvals")
    st.caption("Review, edit, approve, or reject pending content. No auto-publishing.")

    pending = get_pending_posts(session)
    if not pending:
        st.info("No posts pending approval.")
        return

    st.write(f"**{len(pending)}** post(s) awaiting review.")

    for post in pending:
        with st.expander(f"#{post.id} — {post.platform.title()} — {post.topic[:60]}"):
            edited_content = st.text_area(
                "Content",
                value=post.content,
                height=180,
                key=f"content_{post.id}",
            )
            tags = hashtags_from_json(post.hashtags)
            tags_str = st.text_input(
                "Hashtags (comma-separated)",
                value=", ".join(tags),
                key=f"tags_{post.id}",
            )

            if post.image_prompt:
                st.write(f"**Image Prompt:** {post.image_prompt}")
            st.caption(
                f"Provider: {post.provider_used or 'N/A'} | Model: {post.model_used or 'N/A'}"
            )
            if post.quality_notes:
                st.caption(f"Quality: {post.quality_notes}")

            b1, b2, b3, b4, b5, b6 = st.columns(6)

            with b1:
                if st.button("Save Edit", key=f"save_{post.id}"):
                    new_tags = [t.strip().lstrip("#") for t in tags_str.split(",") if t.strip()]
                    ok, msg = update_content(session, post.id, edited_content, new_tags)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

            with b2:
                if st.button("Approve", key=f"approve_{post.id}", type="primary"):
                    ok, msg = approve_post(session, post.id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with b3:
                if st.button("Reject", key=f"reject_{post.id}"):
                    ok, msg = reject_post(session, post.id)
                    if ok:
                        st.warning(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with b4:
                if st.button("Regenerate", key=f"regen_{post.id}"):
                    with st.spinner("Regenerating..."):
                        agent = ContentPilotAgent(session)
                        ok, msg, new_id = regenerate_post(session, post.id, agent)
                        if ok:
                            st.success(f"{msg} New post ID: {new_id}")
                            st.rerun()
                        else:
                            st.error(msg)

            with b5:
                if st.button("Schedule", key=f"schedule_{post.id}"):
                    ok, msg = schedule_post(session, post.id, datetime.utcnow())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with b6:
                if st.button("Mark Published", key=f"publish_{post.id}"):
                    ok, msg = mark_published(session, post.id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

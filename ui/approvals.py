"""Approvals page."""

from datetime import datetime

import streamlit as st
from sqlalchemy.orm import Session

from core.agent import ContentPilotAgent
from core.approvals import (
    approve_post,
    get_pending_posts,
    regenerate_post,
    reject_post,
    save_feedback,
    schedule_post,
    update_content,
)
from core.utils import format_user_error, hashtags_from_json
from ui.components import (
    render_page_header,
    render_platform_badge,
    render_queue_card,
    render_section_header,
    render_status_badge,
)


def _render_post_detail(session: Session, post) -> None:
    edited_content = st.text_area(
        "Content",
        value=post.content,
        height=180,
        key=f"dlg_content_{post.id}",
    )
    tags = hashtags_from_json(post.hashtags)
    tags_str = st.text_input(
        "Hashtags (comma-separated)",
        value=", ".join(tags),
        key=f"dlg_tags_{post.id}",
    )
    reject_reason = st.text_input("Rejection reason (optional)", key=f"dlg_reject_{post.id}")
    feedback = st.text_area(
        "Human feedback",
        value=post.manual_feedback or "",
        key=f"dlg_feedback_{post.id}",
    )
    quality_score = st.slider(
        "Quality score (1-10)",
        min_value=1,
        max_value=10,
        value=post.training_score or 5,
        key=f"dlg_quality_{post.id}",
    )

    if post.image_prompt:
        st.write(f"**Image Prompt:** {post.image_prompt}")
    st.caption(f"Provider: {post.provider_used or 'N/A'} | Model: {post.model_used or 'N/A'}")
    if post.quality_notes:
        st.caption(f"Quality: {post.quality_notes}")

    b1, b2, b3, b4, b5, b6 = st.columns(6)
    with b1:
        if st.button("Save Edit", key=f"dlg_save_{post.id}"):
            new_tags = [t.strip().lstrip("#") for t in tags_str.split(",") if t.strip()]
            ok, msg = update_content(session, post.id, edited_content, new_tags)
            st.success(msg) if ok else st.error(msg)
    with b2:
        if st.button("Save Feedback", key=f"dlg_fb_{post.id}"):
            ok, msg = save_feedback(session, post.id, feedback, quality_score)
            st.success(msg) if ok else st.error(msg)
    with b3:
        if st.button("Approve", key=f"dlg_approve_{post.id}", type="primary"):
            save_feedback(session, post.id, feedback, quality_score)
            ok, msg = approve_post(session, post.id)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    with b4:
        if st.button("Reject", key=f"dlg_reject_btn_{post.id}"):
            ok, msg = reject_post(session, post.id, reject_reason)
            if ok:
                st.warning(msg)
                st.rerun()
            else:
                st.error(msg)
    with b5:
        if st.button("Regenerate", key=f"dlg_regen_{post.id}"):
            with st.spinner("Regenerating..."):
                agent = ContentPilotAgent(session)
                ok, msg, new_id = regenerate_post(session, post.id, agent)
                if ok:
                    st.success(f"{msg} New post ID: {new_id}")
                    st.rerun()
                else:
                    st.error(msg)
    with b6:
        if st.button("Schedule", key=f"dlg_schedule_{post.id}"):
            ok, msg = schedule_post(session, post.id, datetime.utcnow())
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def render(session: Session) -> None:
    render_page_header("Approvals", "Review, edit, approve, or reject pending content. No auto-publishing.")

    pending = get_pending_posts(session)
    if not pending:
        st.info("No posts pending approval.")
        return

    st.markdown(f"**{len(pending)}** post(s) awaiting review.")
    render_section_header("Approval Queue")

    for post in pending:
        badges = f"{render_platform_badge(post.platform)} {render_status_badge('Pending', 'pending')}"
        render_queue_card(
            f"#{post.id} — {post.topic[:60]}",
            badges,
            post.content or "",
            f"Provider: {post.provider_used or 'N/A'} · {post.created_at.strftime('%Y-%m-%d %H:%M') if post.created_at else ''}",
        )
        ac1, ac2, ac3 = st.columns([1, 1, 4])
        with ac1:
            view = st.button("View Details", key=f"view_{post.id}", use_container_width=True)
        with ac2:
            if st.button("Quick Approve", key=f"quick_{post.id}", type="primary", use_container_width=True):
                ok, msg = approve_post(session, post.id)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        if view:
            if hasattr(st, "dialog"):
                @st.dialog(f"Post #{post.id} — Review")  # noqa: B023
                def _approval_dialog():
                    _render_post_detail(session, post)

                _approval_dialog()
            else:
                with st.expander(f"Details — #{post.id}", expanded=True):
                    _render_post_detail(session, post)

        st.write("")

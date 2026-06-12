"""Training Data page — AI training examples and exports."""

import streamlit as st
from sqlalchemy.orm import Session

from core.training_data import (
    get_all_training_examples,
    get_events_for_post,
    get_training_stats,
    mark_training_example_used,
    update_training_feedback,
)
from core.utils import format_user_error
from ui.components import (
    render_metrics_grid,
    render_page_header,
    render_section_header,
    render_status_badge,
)


def render(session: Session) -> None:
    render_page_header("Training Data", "Manage training examples for fine-tuning, RAG, and brand learning.")

    stats = get_training_stats(session)
    render_metrics_grid([
        ("Total Examples", stats["total"], "◎"),
        ("Approved", stats["approved"], "✓"),
        ("Published", stats["published"], "📤"),
        ("Rejected", stats["rejected"], "✗"),
        ("Avg Quality", stats["avg_quality_score"] or "N/A", "★"),
    ])

    st.markdown('<div class="cp-card">', unsafe_allow_html=True)
    render_section_header("Export Training Data")
    export_source = st.radio(
        "Export Source",
        ["Content posts", "Chatbot", "Both"],
        horizontal=True,
    )
    include_rejected = st.checkbox("Include rejected examples", value=False)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export JSONL", use_container_width=True):
            from core.chat_database import export_chatbot_training_jsonl, export_combined_training_jsonl
            from core.training_data import export_training_data_jsonl

            if export_source == "Content posts":
                data = export_training_data_jsonl(session, include_rejected=include_rejected)
                filename = "training_data_posts.jsonl"
            elif export_source == "Chatbot":
                data = export_chatbot_training_jsonl(session, include_rejected=include_rejected)
                filename = "training_data_chatbot.jsonl"
            else:
                data = export_combined_training_jsonl(session, include_rejected=include_rejected)
                filename = "training_data_combined.jsonl"
            st.download_button("Download JSONL", data=data, file_name=filename, mime="application/jsonl")
    with col2:
        if export_source == "Content posts" and st.button("Export CSV", use_container_width=True):
            from core.training_data import export_training_data_csv

            data = export_training_data_csv(session, include_rejected=include_rejected)
            st.download_button("Download CSV", data=data, file_name="training_data.csv", mime="text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

    render_section_header("Training Examples")
    search = st.text_input("Search", placeholder="Filter by platform, status...", key="td_search")

    examples = get_all_training_examples(session)
    if search:
        q = search.lower()
        examples = [
            ex for ex in examples
            if q in (ex.platform or "").lower()
            or q in (ex.approval_status or "").lower()
            or q in (ex.input_prompt or "").lower()[:100]
        ]

    if not examples:
        st.info("No training examples yet. Approve posts to create training data.")
        return

    for ex in examples:
        badge = render_status_badge(ex.approval_status or "unknown", ex.approval_status or "muted")
        st.markdown(
            f'<div class="cp-card" style="padding:14px 16px;">'
            f'<div style="display:flex;justify-content:space-between;">'
            f'<strong>#{ex.id} — Post {ex.post_id} — {ex.platform}</strong> {badge}</div>'
            f'<div style="font-size:0.8125rem;color:#6B7280;margin-top:6px;">'
            f'Quality: {ex.quality_score or "N/A"} · Used: {ex.used_for_training}</div></div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"View & Edit — #{ex.id}"):
            st.caption(f"Input: {(ex.input_prompt or '')[:200]}...")
            st.caption(f"Output: {(ex.ai_output or ex.final_edited_output or '')[:200]}...")

            feedback = st.text_area(
                "Human Feedback",
                value=ex.human_feedback or "",
                key=f"feedback_{ex.id}",
            )
            score = st.slider(
                "Quality Score (1-10)",
                min_value=1,
                max_value=10,
                value=ex.quality_score or 5,
                key=f"score_{ex.id}",
            )

            b1, b2 = st.columns(2)
            with b1:
                if st.button("Save Feedback", key=f"save_fb_{ex.id}", use_container_width=True):
                    try:
                        update_training_feedback(session, ex.post_id, feedback, score)
                        session.commit()
                        st.success("Feedback saved.")
                        st.rerun()
                    except Exception as exc:
                        session.rollback()
                        st.error(format_user_error("Failed to save feedback.", exc))
            with b2:
                if not ex.used_for_training and st.button("Mark Used for Training", key=f"used_{ex.id}", use_container_width=True):
                    mark_training_example_used(session, ex.id)
                    session.commit()
                    st.success("Marked as used for training.")
                    st.rerun()

            with st.expander("Event History"):
                events = get_events_for_post(session, ex.post_id)
                if events:
                    for ev in events:
                        st.caption(
                            f"{ev.created_at.strftime('%Y-%m-%d %H:%M') if ev.created_at else ''} "
                            f"— {ev.event_type}"
                        )
                else:
                    st.caption("No events recorded.")

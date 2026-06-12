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


def render(session: Session) -> None:
    st.title("Training Data")
    st.caption("Manage training examples for future fine-tuning, RAG, and brand learning.")

    stats = get_training_stats(session)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Examples", stats["total"])
    c2.metric("Approved", stats["approved"])
    c3.metric("Published", stats["published"])
    c4.metric("Rejected", stats["rejected"])
    c5.metric("Avg Quality", stats["avg_quality_score"] or "N/A")

    st.divider()
    st.subheader("Export Training Data")
    include_rejected = st.checkbox("Include rejected examples", value=False)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export JSONL"):
            from core.training_data import export_training_data_jsonl

            data = export_training_data_jsonl(session, include_rejected=include_rejected)
            st.download_button(
                "Download JSONL",
                data=data,
                file_name="training_data.jsonl",
                mime="application/jsonl",
            )
    with col2:
        if st.button("Export CSV"):
            from core.training_data import export_training_data_csv

            data = export_training_data_csv(session, include_rejected=include_rejected)
            st.download_button(
                "Download CSV",
                data=data,
                file_name="training_data.csv",
                mime="text/csv",
            )

    st.divider()
    st.subheader("Training Examples")
    examples = get_all_training_examples(session)
    if not examples:
        st.info("No training examples yet. Approve posts to create training data.")
        return

    for ex in examples:
        with st.expander(
            f"#{ex.id} — Post {ex.post_id} — {ex.platform} — {ex.approval_status}"
        ):
            st.caption(f"Quality: {ex.quality_score or 'N/A'} | Used for training: {ex.used_for_training}")

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
                if st.button("Save Feedback", key=f"save_fb_{ex.id}"):
                    try:
                        update_training_feedback(session, ex.post_id, feedback, score)
                        session.commit()
                        st.success("Feedback saved.")
                        st.rerun()
                    except Exception as exc:
                        session.rollback()
                        st.error(format_user_error("Failed to save feedback.", exc))

            with b2:
                if not ex.used_for_training and st.button("Mark Used for Training", key=f"used_{ex.id}"):
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

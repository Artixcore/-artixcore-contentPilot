"""AI training data service for fine-tuning and brand learning."""

import json
from io import StringIO

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.models import Post, TrainingExample
from core.utils import log_content_event


class TrainingDataError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _get_post(session: Session, post_id: int) -> Post:
    post = session.get(Post, post_id)
    if not post:
        raise TrainingDataError(f"Post {post_id} not found.")
    return post


def _get_or_create_example(session: Session, post: Post) -> TrainingExample:
    example = (
        session.query(TrainingExample)
        .filter(TrainingExample.post_id == post.id)
        .order_by(TrainingExample.id.desc())
        .first()
    )
    if example:
        return example
    example = TrainingExample(
        post_id=post.id,
        platform=post.platform,
        task_type="generate_post",
        input_prompt=post.input_prompt,
        system_prompt=post.system_prompt,
        ai_output=post.raw_ai_response,
        final_edited_output=post.content,
        approval_status=post.status,
    )
    session.add(example)
    session.flush()
    return example


def create_training_example_from_post(session: Session, post_id: int) -> TrainingExample:
    post = _get_post(session, post_id)
    example = _get_or_create_example(session, post)
    example.input_prompt = post.input_prompt
    example.system_prompt = post.system_prompt
    example.ai_output = post.raw_ai_response
    example.final_edited_output = post.content
    example.platform = post.platform
    example.approval_status = post.status
    if post.training_score is not None:
        example.quality_score = post.training_score
    if post.manual_feedback:
        example.human_feedback = post.manual_feedback
    session.flush()
    return example


def update_training_feedback(
    session: Session,
    post_id: int,
    human_feedback: str | None = None,
    quality_score: int | None = None,
) -> TrainingExample:
    post = _get_post(session, post_id)
    if quality_score is not None and (quality_score < 1 or quality_score > 10):
        raise TrainingDataError("Quality score must be between 1 and 10.")

    if human_feedback is not None:
        post.manual_feedback = human_feedback
    if quality_score is not None:
        post.training_score = quality_score

    example = _get_or_create_example(session, post)
    if human_feedback is not None:
        example.human_feedback = human_feedback
    if quality_score is not None:
        example.quality_score = quality_score

    log_content_event(
        session,
        post_id,
        "feedback_added",
        {"human_feedback": human_feedback, "quality_score": quality_score},
    )
    session.flush()
    return example


def mark_training_example_used(session: Session, example_id: int) -> TrainingExample:
    example = session.get(TrainingExample, example_id)
    if not example:
        raise TrainingDataError(f"Training example {example_id} not found.")
    example.used_for_training = True
    session.flush()
    return example


def update_training_on_approval(session: Session, post_id: int, status: str) -> None:
    post = _get_post(session, post_id)
    example = _get_or_create_example(session, post)
    example.final_edited_output = post.content
    example.approval_status = status
    if post.training_score is not None:
        example.quality_score = post.training_score
    if post.manual_feedback:
        example.human_feedback = post.manual_feedback
    session.flush()


def _query_examples(session: Session, include_rejected: bool = False) -> list[TrainingExample]:
    query = session.query(TrainingExample)
    if not include_rejected:
        query = query.filter(TrainingExample.approval_status != "rejected")
    return query.order_by(TrainingExample.created_at.desc()).all()


def export_training_data_jsonl(session: Session, include_rejected: bool = False) -> str:
    examples = _query_examples(session, include_rejected=include_rejected)
    lines = []
    for ex in examples:
        if not ex.system_prompt or not ex.input_prompt:
            continue
        output = ex.final_edited_output or ex.ai_output or ""
        if not output:
            continue
        record = {
            "messages": [
                {"role": "system", "content": ex.system_prompt},
                {"role": "user", "content": ex.input_prompt},
                {"role": "assistant", "content": output},
            ],
            "metadata": {
                "platform": ex.platform,
                "quality_score": ex.quality_score,
                "approval_status": ex.approval_status,
            },
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    return "\n".join(lines) + ("\n" if lines else "")


def export_training_data_csv(session: Session, include_rejected: bool = False) -> str:
    examples = _query_examples(session, include_rejected=include_rejected)
    rows = [
        {
            "id": ex.id,
            "post_id": ex.post_id,
            "platform": ex.platform,
            "task_type": ex.task_type,
            "input_prompt": ex.input_prompt or "",
            "system_prompt": ex.system_prompt or "",
            "ai_output": ex.ai_output or "",
            "final_edited_output": ex.final_edited_output or "",
            "human_feedback": ex.human_feedback or "",
            "approval_status": ex.approval_status,
            "quality_score": ex.quality_score,
            "engagement_score": ex.engagement_score,
            "used_for_training": ex.used_for_training,
            "created_at": ex.created_at.isoformat() if ex.created_at else "",
        }
        for ex in examples
    ]
    if not rows:
        rows = [{"id": "", "post_id": "", "platform": "", "approval_status": ""}]
    return pd.DataFrame(rows).to_csv(index=False)


def get_training_stats(session: Session) -> dict:
    total = session.query(func.count(TrainingExample.id)).scalar() or 0
    approved = (
        session.query(func.count(TrainingExample.id))
        .filter(TrainingExample.approval_status == "approved")
        .scalar()
        or 0
    )
    published = (
        session.query(func.count(TrainingExample.id))
        .filter(TrainingExample.approval_status == "published")
        .scalar()
        or 0
    )
    rejected = (
        session.query(func.count(TrainingExample.id))
        .filter(TrainingExample.approval_status == "rejected")
        .scalar()
        or 0
    )
    avg_score = (
        session.query(func.avg(TrainingExample.quality_score))
        .filter(TrainingExample.quality_score.isnot(None))
        .scalar()
    )
    return {
        "total": total,
        "approved": approved,
        "published": published,
        "rejected": rejected,
        "avg_quality_score": round(float(avg_score), 2) if avg_score else None,
    }


def get_events_for_post(session: Session, post_id: int) -> list:
    from core.models import ContentEvent

    return (
        session.query(ContentEvent)
        .filter(ContentEvent.post_id == post_id)
        .order_by(ContentEvent.created_at.desc())
        .all()
    )


def get_all_training_examples(session: Session) -> list[TrainingExample]:
    return session.query(TrainingExample).order_by(TrainingExample.created_at.desc()).all()

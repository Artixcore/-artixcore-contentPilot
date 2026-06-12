"""Tests for training data service."""

import json

from core.approvals import approve_post
from core.models import Post, TrainingExample
from core.training_data import (
    create_training_example_from_post,
    export_training_data_jsonl,
    update_training_feedback,
)


def _make_post(db_session, status="approved"):
    post = Post(
        platform="linkedin",
        topic="AI automation",
        content="Final edited content for training.",
        status=status,
        input_prompt="Generate a post about AI",
        system_prompt="You are Artixcore content assistant.",
        raw_ai_response='{"content": "AI draft"}',
        provider_used="openai",
        model_used="gpt-4.1-mini",
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


def test_create_training_example_from_approved_post(db_session):
    post = _make_post(db_session)
    example = create_training_example_from_post(db_session, post.id)
    db_session.commit()

    assert example.post_id == post.id
    assert example.input_prompt == post.input_prompt
    assert example.final_edited_output == post.content


def test_update_human_feedback(db_session):
    post = _make_post(db_session)
    create_training_example_from_post(db_session, post.id)
    example = update_training_feedback(
        db_session, post.id, human_feedback="Great tone", quality_score=9
    )
    db_session.commit()

    assert example.human_feedback == "Great tone"
    assert example.quality_score == 9

    refreshed = db_session.get(Post, post.id)
    assert refreshed.training_score == 9
    assert refreshed.manual_feedback == "Great tone"


def test_update_quality_score(db_session):
    post = _make_post(db_session)
    update_training_feedback(db_session, post.id, quality_score=8)
    db_session.commit()

    example = db_session.query(TrainingExample).filter_by(post_id=post.id).first()
    assert example.quality_score == 8


def test_export_jsonl_excludes_rejected_by_default(db_session):
    approved = _make_post(db_session, status="approved")
    approve_post(db_session, approved.id)
    create_training_example_from_post(db_session, approved.id)

    rejected = _make_post(db_session, status="rejected")
    ex = create_training_example_from_post(db_session, rejected.id)
    ex.approval_status = "rejected"
    db_session.commit()

    data = export_training_data_jsonl(db_session, include_rejected=False)
    lines = [line for line in data.strip().split("\n") if line]
    assert len(lines) >= 1
    for line in lines:
        record = json.loads(line)
        assert record["metadata"]["approval_status"] != "rejected"

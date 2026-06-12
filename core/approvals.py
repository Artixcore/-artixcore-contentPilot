"""Post approval workflow helpers."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.agent import ContentPilotAgent
from core.models import POST_STATUSES, Post
from core.training_data import create_training_example_from_post, update_training_feedback
from core.utils import hashtags_from_json, hashtags_to_json, log_content_event


class ApprovalError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _get_post(session: Session, post_id: int) -> Post:
    post = session.get(Post, post_id)
    if not post:
        raise ApprovalError(f"Post {post_id} not found.")
    return post


def approve_post(
    session: Session,
    post_id: int,
    approved_by: str = "user",
) -> tuple[bool, str]:
    try:
        post = _get_post(session, post_id)
        post.status = "approved"
        post.approved_at = datetime.now(timezone.utc)
        post.approved_by = approved_by
        from core.training_data import update_training_on_approval

        create_training_example_from_post(session, post_id)
        update_training_on_approval(session, post_id, "approved")
        log_content_event(session, post_id, "approved", {"approved_by": approved_by})
        session.commit()
        return True, "Post approved successfully."
    except ApprovalError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to approve post. Please try again."


def reject_post(session: Session, post_id: int, reason: str = "") -> tuple[bool, str]:
    try:
        post = _get_post(session, post_id)
        post.status = "rejected"
        if reason:
            post.rejected_reason = reason
            note = f"Rejected: {reason}"
            post.quality_notes = (
                f"{post.quality_notes}\n{note}" if post.quality_notes else note
            )
        create_training_example_from_post(session, post_id)
        from core.training_data import update_training_on_approval

        update_training_on_approval(session, post_id, "rejected")
        log_content_event(session, post_id, "rejected", {"reason": reason})
        session.commit()
        return True, "Post rejected."
    except ApprovalError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to reject post. Please try again."


def schedule_post(
    session: Session, post_id: int, scheduled_at: datetime | None = None
) -> tuple[bool, str]:
    try:
        post = _get_post(session, post_id)
        post.status = "scheduled"
        post.scheduled_at = scheduled_at or datetime.now(timezone.utc)
        log_content_event(session, post_id, "scheduled", {})
        session.commit()
        return True, "Post marked as scheduled."
    except ApprovalError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to schedule post. Please try again."


def update_content(
    session: Session,
    post_id: int,
    content: str,
    hashtags: list[str] | None = None,
) -> tuple[bool, str]:
    try:
        post = _get_post(session, post_id)
        if not content or not content.strip():
            raise ApprovalError("Content cannot be empty.")
        post.content = content.strip()
        if hashtags is not None:
            post.hashtags = hashtags_to_json(hashtags)
        post.revision_count = (post.revision_count or 0) + 1
        log_content_event(
            session,
            post_id,
            "edited",
            {"revision_count": post.revision_count},
        )
        session.commit()
        return True, "Post content updated."
    except ApprovalError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to update post. Please try again."


def save_feedback(
    session: Session,
    post_id: int,
    human_feedback: str | None = None,
    quality_score: int | None = None,
) -> tuple[bool, str]:
    try:
        update_training_feedback(session, post_id, human_feedback, quality_score)
        session.commit()
        return True, "Feedback saved."
    except Exception as exc:
        session.rollback()
        from core.training_data import TrainingDataError

        if isinstance(exc, TrainingDataError):
            return False, exc.message
        return False, "Failed to save feedback."


def regenerate_post(
    session: Session,
    post_id: int,
    agent: ContentPilotAgent,
) -> tuple[bool, str, int | None]:
    try:
        post = _get_post(session, post_id)
        generated = agent.generate_post(
            platform=post.platform,
            topic=post.topic,
            goal=post.goal,
            tone=post.tone,
            language=post.language,
            cta=post.cta,
            provider_mode="auto",
        )
        post.status = "rejected"
        note = "Superseded by regenerated post."
        post.quality_notes = (
            f"{post.quality_notes}\n{note}" if post.quality_notes else note
        )
        session.commit()
        return True, "New post generated and pending approval.", generated.post_id
    except Exception as exc:
        session.rollback()
        from core.agent import AgentValidationError

        if isinstance(exc, AgentValidationError):
            return False, exc.message, None
        return False, "Failed to regenerate post. Please try again.", None


def get_pending_posts(session: Session) -> list[Post]:
    return (
        session.query(Post)
        .filter(Post.status == "pending_approval")
        .order_by(Post.created_at.desc())
        .all()
    )


def get_post_by_id(session: Session, post_id: int) -> Post | None:
    return session.get(Post, post_id)

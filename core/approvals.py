"""Post approval workflow helpers."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.agent import ContentPilotAgent
from core.models import POST_STATUSES, Post
from core.utils import hashtags_from_json, hashtags_to_json


class ApprovalError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _get_post(session: Session, post_id: int) -> Post:
    post = session.get(Post, post_id)
    if not post:
        raise ApprovalError(f"Post {post_id} not found.")
    return post


def _validate_status(status: str) -> None:
    if status not in POST_STATUSES:
        raise ApprovalError(f"Invalid status: {status}")


def approve_post(session: Session, post_id: int) -> tuple[bool, str]:
    try:
        post = _get_post(session, post_id)
        post.status = "approved"
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
            note = f"Rejected: {reason}"
            post.quality_notes = (
                f"{post.quality_notes}\n{note}" if post.quality_notes else note
            )
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
        session.commit()
        return True, "Post marked as scheduled."
    except ApprovalError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to schedule post. Please try again."


def mark_published(session: Session, post_id: int) -> tuple[bool, str]:
    try:
        post = _get_post(session, post_id)
        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
        session.commit()
        return True, "Post marked as published (manual post)."
    except ApprovalError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to mark post as published. Please try again."


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
        session.commit()
        return True, "Post content updated."
    except ApprovalError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to update post. Please try again."


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

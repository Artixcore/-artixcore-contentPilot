"""Publishing service — manual publish with platform connectors."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.models import PLATFORMS, Post, PublishingLog
from core.training_data import update_training_on_approval
from core.utils import log_content_event, sanitize_payload
from publishers import get_all_publishers
from publishers.base import BasePublisher

logger = logging.getLogger(__name__)

PUBLISHABLE_STATUSES = frozenset({"approved", "scheduled"})


class PublishError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def get_publisher(platform_name: str) -> BasePublisher | None:
    return get_all_publishers().get(platform_name)


def get_publisher_statuses() -> dict[str, bool]:
    return {name: pub.is_configured() for name, pub in get_all_publishers().items()}


def _get_post(session: Session, post_id: int) -> Post:
    post = session.get(Post, post_id)
    if not post:
        raise PublishError(f"Post {post_id} not found.")
    return post


def _log_publish(
    session: Session,
    post_id: int,
    platform: str,
    result: dict,
    request_payload: dict | None = None,
) -> None:
    log = PublishingLog(
        post_id=post_id,
        platform=platform,
        success=result.get("success", False),
        external_post_id=result.get("external_post_id") or None,
        external_post_url=result.get("external_post_url") or None,
        error_message=result.get("error") or None,
        request_payload_sanitized=sanitize_payload(request_payload or {}),
        response_payload_sanitized=sanitize_payload(result.get("raw_response", {})),
    )
    session.add(log)


def publish_post(
    session: Session,
    post_id: int,
    platform_name: str,
    image_url: str | None = None,
) -> dict:
    post = _get_post(session, post_id)
    if post.status not in PUBLISHABLE_STATUSES:
        raise PublishError(
            f"Only approved or scheduled posts can be published. Current status: {post.status}."
        )

    publisher = get_publisher(platform_name)
    if not publisher:
        raise PublishError(f"Unknown platform: {platform_name}.")

    if not publisher.is_configured():
        raise PublishError(
            f"{platform_name.replace('_', ' ').title()} is not configured. "
            "Check Publishing Settings for required environment variables."
        )

    content = post.content
    request_payload = {"platform": platform_name, "content_preview": content[:200]}

    if platform_name == "instagram":
        if not image_url or not image_url.strip():
            result = publisher.publish_image(content, "")
        else:
            result = publisher.publish_image(content, image_url.strip())
    elif platform_name == "website_blog":
        parsed = {}
        if post.parsed_ai_response:
            try:
                parsed = json.loads(post.parsed_ai_response)
            except json.JSONDecodeError:
                parsed = {}
        result = publisher.publish_text(
            content,
            title=parsed.get("title", post.topic),
            slug=parsed.get("slug"),
            meta_description=parsed.get("meta_description", content[:160]),
            topic=post.topic,
        )
    else:
        result = publisher.publish_text(content)

    _log_publish(session, post_id, platform_name, result, request_payload)

    if result.get("success"):
        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
        post.published_by_platform = platform_name
        post.external_post_id = result.get("external_post_id") or None
        post.external_post_url = result.get("external_post_url") or None
        post.publish_error = None
        post.publish_raw_response = json.dumps(result.get("raw_response", {}), ensure_ascii=False)
        update_training_on_approval(session, post_id, "published")
        log_content_event(
            session,
            post_id,
            "published",
            {"platform": platform_name, "external_post_id": result.get("external_post_id")},
        )
        session.commit()
    else:
        post.publish_error = result.get("error", "Publish failed.")
        post.publish_raw_response = json.dumps(result.get("raw_response", {}), ensure_ascii=False)
        log_content_event(
            session,
            post_id,
            "publish_failed",
            {"platform": platform_name, "error": result.get("error")},
        )
        session.commit()

    return result


def mark_as_manually_posted(
    session: Session,
    post_id: int,
    platform_name: str,
) -> tuple[bool, str]:
    try:
        post = _get_post(session, post_id)
        if post.status not in PUBLISHABLE_STATUSES:
            return False, f"Only approved or scheduled posts can be marked. Status: {post.status}."

        if platform_name not in PLATFORMS:
            return False, f"Unknown platform: {platform_name}."

        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
        post.published_by_platform = platform_name
        post.publish_error = None
        update_training_on_approval(session, post_id, "published")
        log_content_event(
            session,
            post_id,
            "manually_posted",
            {"platform": platform_name},
        )
        _log_publish(
            session,
            post_id,
            platform_name,
            {
                "success": True,
                "external_post_id": "",
                "external_post_url": "",
                "error": "",
                "raw_response": {"manual": True},
            },
            {"manual": True},
        )
        session.commit()
        return True, "Post marked as manually published."
    except PublishError as exc:
        return False, exc.message
    except Exception:
        session.rollback()
        return False, "Failed to mark post as manually published."


def get_publishable_posts(session: Session) -> list[Post]:
    return (
        session.query(Post)
        .filter(Post.status.in_(list(PUBLISHABLE_STATUSES)))
        .order_by(Post.created_at.desc())
        .all()
    )

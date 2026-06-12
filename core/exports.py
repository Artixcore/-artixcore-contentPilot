"""Export posts to CSV, Markdown, and JSON."""

import json
from io import StringIO

import pandas as pd
from sqlalchemy.orm import Session

from core.models import Post
from core.utils import hashtags_from_json


def filter_posts(
    session: Session,
    filter_type: str = "all",
    platform: str | None = None,
) -> list[Post]:
    query = session.query(Post)
    filter_type = (filter_type or "all").lower()

    if filter_type == "approved":
        query = query.filter(Post.status == "approved")
    elif filter_type == "pending":
        query = query.filter(Post.status == "pending_approval")
    elif filter_type == "published":
        query = query.filter(Post.status == "published")
    elif filter_type == "rejected":
        query = query.filter(Post.status == "rejected")

    if platform and platform != "all":
        query = query.filter(Post.platform == platform)

    return query.order_by(Post.created_at.desc()).all()


def _post_to_dict(post: Post) -> dict:
    return {
        "id": post.id,
        "platform": post.platform,
        "topic": post.topic,
        "goal": post.goal,
        "tone": post.tone,
        "language": post.language,
        "cta": post.cta,
        "content": post.content,
        "hashtags": hashtags_from_json(post.hashtags),
        "image_prompt": post.image_prompt,
        "status": post.status,
        "provider_used": post.provider_used,
        "model_used": post.model_used,
        "quality_notes": post.quality_notes,
        "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


def export_csv(posts: list[Post]) -> str:
    if not posts:
        rows = [{
            "id": "",
            "platform": "",
            "topic": "",
            "content": "",
            "status": "",
        }]
    else:
        rows = []
        for post in posts:
            row = _post_to_dict(post)
            row["hashtags"] = ", ".join(row["hashtags"])
            rows.append(row)
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def export_markdown(posts: list[Post]) -> str:
    if not posts:
        return "# ContentPilot Export\n\nNo posts to export.\n"

    lines = ["# ContentPilot Export\n"]
    for post in posts:
        tags = " ".join(f"#{h.lstrip('#')}" for h in hashtags_from_json(post.hashtags))
        lines.append(f"## Post #{post.id} — {post.platform.title()}\n")
        lines.append(f"- **Topic:** {post.topic}")
        lines.append(f"- **Status:** {post.status}")
        lines.append(f"- **Provider:** {post.provider_used or 'N/A'}")
        lines.append(f"- **Created:** {post.created_at}\n")
        lines.append("### Content\n")
        lines.append(post.content)
        lines.append("")
        if tags:
            lines.append(f"**Hashtags:** {tags}\n")
        if post.image_prompt:
            lines.append(f"**Image Prompt:** {post.image_prompt}\n")
        if post.quality_notes:
            lines.append(f"**Quality Notes:** {post.quality_notes}\n")
        lines.append("---\n")
    return "\n".join(lines)


def export_json(posts: list[Post]) -> str:
    data = [_post_to_dict(p) for p in posts]
    return json.dumps(data, indent=2, ensure_ascii=False)

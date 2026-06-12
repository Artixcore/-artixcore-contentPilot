"""Post analytics service (MVP — manual entry and future platform fetch)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.models import PostAnalytics


def get_post_analytics(session: Session, post_id: int) -> list[PostAnalytics]:
    return (
        session.query(PostAnalytics)
        .filter(PostAnalytics.post_id == post_id)
        .order_by(PostAnalytics.captured_at.desc())
        .all()
    )


def save_manual_analytics(
    session: Session,
    post_id: int,
    platform: str,
    external_post_id: str | None = None,
    impressions: int | None = None,
    reach: int | None = None,
    likes: int | None = None,
    comments: int | None = None,
    shares: int | None = None,
    clicks: int | None = None,
    engagement_rate: float | None = None,
) -> PostAnalytics:
    record = PostAnalytics(
        post_id=post_id,
        platform=platform,
        external_post_id=external_post_id,
        impressions=impressions,
        reach=reach,
        likes=likes,
        comments=comments,
        shares=shares,
        clicks=clicks,
        engagement_rate=engagement_rate,
        captured_at=datetime.now(timezone.utc),
    )
    session.add(record)
    session.flush()
    return record

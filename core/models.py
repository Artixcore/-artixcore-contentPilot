"""SQLAlchemy ORM models for ContentPilot."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    page_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website_url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    services: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_cta: Mapped[str] = mapped_column(Text, nullable=False)
    forbidden_style: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str] = mapped_column(String(512), nullable=False)
    goal: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    tone: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="English")
    cta: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hashtags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    image_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    provider_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    platforms: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    posts_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )


class ProviderLog(Base):
    __tablename__ = "provider_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, default="generate")
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


POST_STATUSES = (
    "draft",
    "pending_approval",
    "approved",
    "scheduled",
    "published",
    "rejected",
    "failed",
)

PLATFORMS = (
    "facebook",
    "instagram",
    "linkedin",
    "twitter",
    "website_blog",
)

DEFAULT_BRAND = {
    "company_name": "Artixcore",
    "page_name": "Artixcore",
    "website_url": "https://artixcore.com",
    "description": (
        "Artixcore is a technology and software company that builds SaaS platforms, "
        "AI systems, websites, mobile applications, automation tools, and business "
        "software for modern companies."
    ),
    "tone": "Confident, professional, visionary, technical, trustworthy, founder-led.",
    "target_audience": (
        "Startup founders, SMEs, SaaS companies, local businesses, eCommerce brands, "
        "agencies, and enterprise clients."
    ),
    "services": (
        "SaaS development, web app development, mobile app development, AI automation, "
        "custom software, business dashboards, CRM, ERP, eCommerce systems, cloud "
        "deployment, API development."
    ),
    "preferred_cta": (
        "Book a consultation, visit Artixcore, start your software journey, "
        "build your next product with Artixcore."
    ),
    "forbidden_style": (
        "Avoid fake guarantees, exaggerated claims, spammy hashtags, childish AI hype, "
        "and overpromising."
    ),
}

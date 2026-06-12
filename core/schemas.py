"""Pydantic schemas for validation and API boundaries."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Platform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    WEBSITE_BLOG = "website_blog"


class PostStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"


class ProviderMode(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"
    FALLBACK = "fallback"
    QUALITY = "quality"


class BrandProfileBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    page_name: str = Field(min_length=1, max_length=255)
    website_url: str = Field(min_length=1, max_length=512)
    description: str = Field(min_length=1)
    tone: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    services: str = Field(min_length=1)
    preferred_cta: str = Field(min_length=1)
    forbidden_style: str = Field(min_length=1)


class BrandProfileUpdate(BrandProfileBase):
    pass


class BrandProfileRead(BrandProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeneratedPost(BaseModel):
    content: str
    hashtags: list[str] = Field(default_factory=list)
    image_prompt: Optional[str] = None
    quality_notes: Optional[str] = None
    provider_used: str
    model_used: Optional[str] = None
    post_id: Optional[int] = None
    platform: str
    topic: str
    saved: bool = True


class PostCreate(BaseModel):
    platform: str
    topic: str
    goal: str = ""
    tone: str = ""
    language: str = "English"
    cta: str = ""
    content: str = ""
    hashtags: list[str] = Field(default_factory=list)
    image_prompt: Optional[str] = None
    status: str = "pending_approval"
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    quality_notes: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        allowed = {p.value for p in Platform}
        if v not in allowed:
            raise ValueError(f"Unsupported platform: {v}. Allowed: {', '.join(sorted(allowed))}")
        return v


class PostRead(BaseModel):
    id: int
    platform: str
    topic: str
    goal: str
    tone: str
    language: str
    cta: str
    content: str
    hashtags: str
    image_prompt: Optional[str] = None
    status: str
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    quality_notes: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostUpdate(BaseModel):
    content: Optional[str] = None
    hashtags: Optional[list[str]] = None
    status: Optional[str] = None
    quality_notes: Optional[str] = None


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    goal: str = ""
    description: str = ""
    platforms: list[str] = Field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    posts_per_week: int = Field(default=3, ge=1, le=50)
    status: str = "draft"


class CampaignRead(BaseModel):
    id: int
    name: str
    goal: str
    description: str
    platforms: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    posts_per_week: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProviderLogRead(BaseModel):
    id: int
    provider: str
    model: Optional[str] = None
    task_type: str
    success: bool
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignIdeas(BaseModel):
    ideas: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    provider_used: str
    model_used: Optional[str] = None

"""Tests for database initialization and models."""

from core.database import get_brand_profile, seed_default_brand_profile
from core.models import DEFAULT_BRAND, Post


def test_tables_created(db_session):
    profile = get_brand_profile(db_session)
    assert profile is not None


def test_default_brand_profile_values(db_session):
    profile = get_brand_profile(db_session)
    assert profile.company_name == DEFAULT_BRAND["company_name"]
    assert profile.website_url == DEFAULT_BRAND["website_url"]
    assert "Artixcore" in profile.description


def test_seed_runs_once(db_session):
    first = seed_default_brand_profile(db_session)
    second = seed_default_brand_profile(db_session)
    assert first.id == second.id


def test_post_creation(db_session):
    post = Post(
        platform="linkedin",
        topic="Test topic",
        goal="Awareness",
        tone="Professional",
        language="English",
        cta="Book a consultation",
        content="Test content for LinkedIn.",
        hashtags='["Artixcore", "SaaS"]',
        status="pending_approval",
        provider_used="mock",
        model_used="mock-v1",
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    assert post.id is not None
    assert post.status == "pending_approval"

    fetched = db_session.get(Post, post.id)
    assert fetched.topic == "Test topic"


def test_post_status_update(db_session):
    post = Post(
        platform="twitter",
        topic="Status test",
        content="Tweet content",
        status="pending_approval",
    )
    db_session.add(post)
    db_session.commit()

    post.status = "approved"
    db_session.commit()
    db_session.refresh(post)
    assert post.status == "approved"

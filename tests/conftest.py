"""Pytest fixtures for ContentPilot tests."""

import pytest
from sqlalchemy.orm import Session

import core.database as db_module
from core.database import get_session, init_db, reset_engine, seed_default_brand_profile


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def db_session() -> Session:
    reset_engine("sqlite:///:memory:")
    init_db()
    session = get_session()
    seed_default_brand_profile(session)
    session.commit()
    yield session
    session.close()
    reset_engine(db_module.DATABASE_URL)


@pytest.fixture
def approved_post(db_session) -> "Post":
    from core.models import Post

    post = Post(
        platform="linkedin",
        topic="Test topic",
        content="Approved content ready to publish.",
        status="approved",
        provider_used="openai",
        model_used="gpt-4.1-mini",
        input_prompt="Generate post",
        system_prompt="Brand voice",
        raw_ai_response='{"content": "draft"}',
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post

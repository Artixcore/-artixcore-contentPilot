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

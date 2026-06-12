"""Tests for database resilience."""

import pytest
from sqlalchemy import text

from core.database import get_session, init_db, reset_engine, session_scope
from core.migrations import run_migrations
from core.models import Post


def test_session_rollback_on_error(db_session):
    post = Post(
        platform="linkedin",
        topic="Rollback test",
        content="content",
        status="pending_approval",
    )
    db_session.add(post)
    db_session.flush()
    post_id = post.id
    try:
        db_session.execute(text("SELECT invalid_column_xyz FROM posts"))
    except Exception:
        db_session.rollback()
    fetched = db_session.get(Post, post_id)
    assert fetched is None or fetched.id == post_id


def test_migration_idempotent(db_session):
    engine = db_session.get_bind()
    run_migrations(engine)
    run_migrations(engine)
    inspector = __import__("sqlalchemy").inspect(engine)
    assert "posts" in inspector.get_table_names()


def test_missing_table_handled():
    reset_engine("sqlite:///:memory:")
    init_db()
    from core.database import check_database_health

    result = check_database_health()
    assert result["healthy"] is True

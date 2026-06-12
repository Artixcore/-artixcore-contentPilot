"""Database initialization and session management."""

import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from core.migrations import run_migrations
from core.models import DEFAULT_BRAND, Base, BrandProfile

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/contentpilot.db")

_engine = None
_SessionLocal = None


def _ensure_data_dir() -> None:
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if db_path != ":memory:":
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)


def get_engine():
    global _engine
    if _engine is None:
        _ensure_data_dir()
        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(DATABASE_URL, connect_args=connect_args)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def get_session() -> Session:
    return get_session_factory()()


@contextmanager
def session_scope():
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    engine = get_engine()
    run_migrations(engine)


def reset_engine(database_url: str | None = None) -> None:
    """Reset engine (used in tests)."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
    if database_url is not None:
        import core.database as db_module

        db_module.DATABASE_URL = database_url


def seed_default_brand_profile(session: Session | None = None) -> BrandProfile | None:
    own_session = session is None
    if own_session:
        session = get_session()
    try:
        existing = session.execute(select(BrandProfile)).scalars().first()
        if existing:
            return existing
        profile = BrandProfile(**DEFAULT_BRAND)
        session.add(profile)
        if own_session:
            session.commit()
            session.refresh(profile)
        else:
            session.flush()
        return profile
    finally:
        if own_session:
            session.close()


def get_brand_profile(session: Session) -> BrandProfile | None:
    return session.execute(select(BrandProfile)).scalars().first()

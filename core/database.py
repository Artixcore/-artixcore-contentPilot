"""Database initialization and session management."""

import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from core.errors import DatabaseError
from core.logging_config import get_logger
from core.migrations import run_migrations
from core.models import DEFAULT_BRAND, Base, BrandProfile
from core.retries import retry_on_sqlite_locked

load_dotenv()

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/contentpilot.db")
DATABASE_TIMEOUT_SECONDS = int(os.getenv("DATABASE_TIMEOUT_SECONDS", "30"))

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
            connect_args["timeout"] = DATABASE_TIMEOUT_SECONDS
        _engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
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


@retry_on_sqlite_locked()
def init_db() -> None:
    """Initialize database with migrations."""
    try:
        engine = get_engine()
        run_migrations(engine)
        logger.info("Database initialized successfully")
    except DatabaseError:
        raise
    except Exception as exc:
        logger.error("Database initialization failed: %s", type(exc).__name__)
        raise DatabaseError(
            "Database is currently unavailable.",
            reason=str(exc),
            user_action="Please check local database file permissions or restart the app.",
            original_exception=exc,
        ) from exc


def reset_engine(database_url: str | None = None) -> None:
    """Reset engine (used in tests)."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
    if database_url is not None:
        import core.database as db_module

        db_module.DATABASE_URL = database_url


def check_database_health() -> dict:
    """Check database reachability and schema."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        required = set(Base.metadata.tables.keys())
        missing = required - tables
        if missing:
            return {
                "healthy": False,
                "message": f"Missing tables: {', '.join(sorted(missing))}",
            }
        return {"healthy": True, "message": "Database is reachable and schema is valid."}
    except OperationalError as exc:
        return {"healthy": False, "message": f"Database locked or unavailable: {type(exc).__name__}"}
    except Exception as exc:
        return {"healthy": False, "message": f"Database check failed: {type(exc).__name__}"}


@retry_on_sqlite_locked()
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

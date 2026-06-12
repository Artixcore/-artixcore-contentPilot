"""Safe startup migrations — add missing tables/columns without deleting data."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from core.models import Base

logger = logging.getLogger(__name__)

# (table_name, column_name, sqlite_column_def)
COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("posts", "external_post_id", "VARCHAR(255)"),
    ("posts", "external_post_url", "VARCHAR(1024)"),
    ("posts", "published_by_platform", "VARCHAR(50)"),
    ("posts", "publish_error", "TEXT"),
    ("posts", "publish_raw_response", "TEXT"),
    ("posts", "input_prompt", "TEXT"),
    ("posts", "system_prompt", "TEXT"),
    ("posts", "raw_ai_response", "TEXT"),
    ("posts", "parsed_ai_response", "TEXT"),
    ("posts", "generation_temperature", "FLOAT"),
    ("posts", "generation_max_tokens", "INTEGER"),
    ("posts", "provider_latency_ms", "INTEGER"),
    ("posts", "provider_error", "TEXT"),
    ("posts", "token_input_estimate", "INTEGER"),
    ("posts", "token_output_estimate", "INTEGER"),
    ("posts", "cost_estimate", "FLOAT"),
    ("posts", "revision_count", "INTEGER DEFAULT 0"),
    ("posts", "parent_post_id", "INTEGER"),
    ("posts", "approved_by", "VARCHAR(255)"),
    ("posts", "approved_at", "DATETIME"),
    ("posts", "rejected_reason", "TEXT"),
    ("posts", "manual_feedback", "TEXT"),
    ("posts", "training_score", "INTEGER"),
    ("provider_logs", "request_payload_sanitized", "TEXT"),
    ("provider_logs", "response_payload_sanitized", "TEXT"),
]


def run_migrations(engine: Engine) -> None:
    """Create missing tables and add missing columns safely."""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table_name, column_name, column_def in COLUMN_MIGRATIONS:
        if table_name not in existing_tables:
            continue
        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        if column_name in existing_columns:
            continue
        stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
            logger.info("Migration: added column %s.%s", table_name, column_name)
        except Exception as exc:
            logger.warning(
                "Migration skipped %s.%s: %s", table_name, column_name, type(exc).__name__
            )

    inspector = inspect(engine)
    for table_name in Base.metadata.tables:
        if table_name not in inspector.get_table_names():
            logger.warning("Table still missing after migration: %s", table_name)

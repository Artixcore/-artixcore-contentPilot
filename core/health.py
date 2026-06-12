"""System health checks."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from core.logging_config import get_log_file_path
from core.utils import mask_secret

HealthStatus = Literal["healthy", "warning", "error"]


@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "message": self.message}


def _provider_configured(env_key: str) -> bool:
    return bool(os.getenv(env_key, "").strip())


def get_database_health_check() -> HealthCheck:
    try:
        from core.database import check_database_health as db_check

        result = db_check()
        if result.get("healthy"):
            return HealthCheck("database", "healthy", result.get("message", "Database is reachable."))
        return HealthCheck(
            "database",
            "error",
            result.get("message", "Database check failed."),
        )
    except Exception as exc:
        return HealthCheck("database", "error", f"Database unavailable: {type(exc).__name__}")


def run_health_checks() -> list[HealthCheck]:
    checks: list[HealthCheck] = []

    checks.append(HealthCheck("app", "healthy", "Application is running."))

    checks.append(get_database_health_check())

    openai_ok = _provider_configured("OPENAI_API_KEY")
    checks.append(HealthCheck(
        "openai",
        "healthy" if openai_ok else "warning",
        "OpenAI configured." if openai_ok else "OpenAI API key not configured.",
    ))

    anthropic_ok = _provider_configured("ANTHROPIC_API_KEY")
    checks.append(HealthCheck(
        "anthropic",
        "healthy" if anthropic_ok else "warning",
        "Anthropic configured." if anthropic_ok else "Anthropic API key not configured.",
    ))

    connector_env = {
        "linkedin": ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN"),
        "twitter": ("X_ACCESS_TOKEN",),
        "facebook": ("META_PAGE_ACCESS_TOKEN", "META_PAGE_ID"),
        "instagram": ("META_PAGE_ACCESS_TOKEN", "META_IG_USER_ID"),
        "website": ("WEBSITE_API_BASE_URL", "WEBSITE_API_TOKEN"),
        "telegram": ("TELEGRAM_BOT_TOKEN",),
    }
    for name, keys in connector_env.items():
        configured = all(_provider_configured(k) for k in keys)
        checks.append(HealthCheck(
            name,
            "healthy" if configured else "warning",
            f"{name.title()} configured." if configured else f"{name.title()} not fully configured.",
        ))

    log_path = get_log_file_path()
    logs_writable = log_path.parent.exists() and os.access(log_path.parent, os.W_OK)
    checks.append(HealthCheck(
        "logs",
        "healthy" if logs_writable else "error",
        "Log directory is writable." if logs_writable else "Cannot write to logs directory.",
    ))

    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_writable = data_dir.exists() and os.access(data_dir, os.W_OK)
    if not data_dir.exists():
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            data_writable = os.access(data_dir, os.W_OK)
        except OSError:
            data_writable = False
    checks.append(HealthCheck(
        "data_directory",
        "healthy" if data_writable else "error",
        "Data directory is writable." if data_writable else "Cannot write to data directory.",
    ))

    return checks


def get_overall_status() -> HealthStatus:
    checks = run_health_checks()
    if any(c.status == "error" for c in checks):
        return "error"
    if any(c.status == "warning" for c in checks):
        return "warning"
    return "healthy"


def format_health_for_display() -> list[dict]:
    """Return health checks safe for UI display (no secrets)."""
    return [c.to_dict() for c in run_health_checks()]

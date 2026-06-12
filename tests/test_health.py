"""Tests for core.health."""

from core.database import check_database_health
from core.health import get_database_health_check, run_health_checks


def test_database_health_check(db_session):
    result = check_database_health()
    assert result["healthy"] is True
    health = get_database_health_check()
    assert health.status == "healthy"


def test_provider_health_check(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    checks = run_health_checks()
    openai = next(c for c in checks if c.name == "openai")
    assert openai.status == "warning"


def test_connector_health_check():
    checks = run_health_checks()
    linkedin = next(c for c in checks if c.name == "linkedin")
    assert linkedin.status in ("healthy", "warning", "error")

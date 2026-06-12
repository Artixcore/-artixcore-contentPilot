"""Tests for publisher error handling."""

from unittest.mock import MagicMock, patch

import httpx

from publishers.linkedin_publisher import LinkedInPublisher
from publishers.x_publisher import XPublisher


def test_linkedin_missing_config_clean_error(monkeypatch):
    monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LINKEDIN_AUTHOR_URN", raising=False)
    pub = LinkedInPublisher()
    result = pub.publish_text("Hello world")
    assert result["success"] is False
    assert "token" in result["error"].lower() or "urn" in result["error"].lower()


def test_x_missing_config_clean_error(monkeypatch):
    monkeypatch.delenv("X_ACCESS_TOKEN", raising=False)
    pub = XPublisher()
    result = pub.publish_text("Hello")
    assert result["success"] is False
    assert "token" in result["error"].lower()


def test_non_2xx_response_clean_error(monkeypatch):
    monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("LINKEDIN_AUTHOR_URN", "urn:li:person:123")
    pub = LinkedInPublisher()

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {"message": "Permission denied"}
    mock_response.text = "Permission denied"

    with patch.object(pub, "_safe_request", return_value=mock_response):
        result = pub.publish_text("Test post content")
    assert result["success"] is False
    assert "403" in result["error"] or "Permission" in result["error"]


def test_timeout_clean_error(monkeypatch):
    monkeypatch.setenv("X_ACCESS_TOKEN", "test-token")
    pub = XPublisher()
    with patch.object(pub, "_safe_request", side_effect=httpx.TimeoutException("timeout")):
        result = pub.publish_text("Short post")
    assert result["success"] is False
    assert "timed out" in result["error"].lower()

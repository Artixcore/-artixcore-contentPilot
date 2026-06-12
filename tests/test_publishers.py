"""Tests for social platform publishers and publishing service."""

import pytest

from core.models import Post
from core.publishing import PublishError, publish_post
from publishers.linkedin_publisher import LinkedInPublisher
from publishers.meta_facebook_publisher import MetaFacebookPublisher
from publishers.meta_instagram_publisher import MetaInstagramPublisher
from publishers.website_publisher import WebsitePublisher
from publishers.x_publisher import XPublisher


def test_linkedin_missing_token_fails():
    pub = LinkedInPublisher()
    pub.access_token = ""
    pub.author_urn = "urn:li:person:123"
    result = pub.publish_text("Hello LinkedIn")
    assert result["success"] is False
    assert "token" in result["error"].lower()


def test_x_missing_token_fails():
    pub = XPublisher()
    pub.access_token = ""
    result = pub.publish_text("Hello X")
    assert result["success"] is False
    assert "token" in result["error"].lower()


def test_x_over_280_characters_fails(monkeypatch):
    monkeypatch.setenv("X_ACCESS_TOKEN", "test-token")
    pub = XPublisher()
    result = pub.publish_text("x" * 281)
    assert result["success"] is False
    assert "280" in result["error"]


def test_facebook_missing_page_token_fails():
    pub = MetaFacebookPublisher()
    pub.page_id = ""
    pub.page_access_token = ""
    result = pub.publish_text("Hello Facebook")
    assert result["success"] is False


def test_instagram_missing_image_url_fails(monkeypatch):
    monkeypatch.setenv("META_IG_USER_ID", "123")
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "token")
    pub = MetaInstagramPublisher()
    result = pub.publish_image("Caption", "")
    assert result["success"] is False
    assert "image" in result["error"].lower()


def test_website_missing_config_fails():
    pub = WebsitePublisher()
    pub.base_url = ""
    pub.api_token = ""
    result = pub.publish_text("Blog content", title="Test")
    assert result["success"] is False
    assert "not configured" in result["error"].lower()


def test_publish_post_rejects_pending_approval(db_session):
    post = Post(
        platform="linkedin",
        topic="Test",
        content="Content",
        status="pending_approval",
    )
    db_session.add(post)
    db_session.commit()

    with pytest.raises(PublishError, match="approved or scheduled"):
        publish_post(db_session, post.id, "linkedin")


def test_publish_post_allows_approved_when_not_configured(db_session):
    post = Post(
        platform="linkedin",
        topic="Test",
        content="Content",
        status="approved",
    )
    db_session.add(post)
    db_session.commit()

    with pytest.raises(PublishError, match="not configured"):
        publish_post(db_session, post.id, "linkedin")

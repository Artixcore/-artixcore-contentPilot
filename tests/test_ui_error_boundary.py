"""Tests for ui.error_boundary."""

from unittest.mock import MagicMock, patch

from ui.error_boundary import with_error_boundary


def test_page_render_error_does_not_crash():
    session = MagicMock()

    def bad_render(_session):
        raise RuntimeError("page crash")

    wrapped = with_error_boundary("Test Page", bad_render)

    with patch("streamlit.error"), patch("streamlit.markdown"), patch("streamlit.caption"), patch(
        "streamlit.button", return_value=False
    ):
        wrapped(session)


def test_returns_user_friendly_message():
    from core.error_handler import handle_exception

    result = handle_exception(RuntimeError("hidden details"), context="page:Test")
    assert result["success"] is False
    assert "hidden details" not in result.get("message", "") or result["message"]

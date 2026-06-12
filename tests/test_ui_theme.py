"""UI theme and asset smoke tests."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_app_css_exists_and_has_core_classes():
    css_path = ROOT / "assets" / "styles" / "app.css"
    assert css_path.is_file(), "assets/styles/app.css must exist"
    css = css_path.read_text(encoding="utf-8")
    assert ".cp-metric-card" in css
    assert ".cp-shell" in css
    assert ".cp-icon-rail" in css
    assert ".cp-bg" in css
    assert '[data-testid="stSidebar"]' in css or "stSidebar" in css
    assert ".block-container" in css
    assert ".cp-shell-rail" not in css
    assert ".cp-page-bg" not in css


def test_no_partial_html_wrappers_in_ui():
    """UI modules must not open/close divs across separate st.markdown calls."""
    ui_dir = ROOT / "ui"
    offenders: list[str] = []
    for path in ui_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "st.markdown('</div>" in text or 'st.markdown("</div>' in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"Partial HTML wrappers found: {offenders}"


def test_bootstrap_theme_injects_cdn(monkeypatch):
    captured: list[str] = []

    def fake_markdown(body: str, unsafe_allow_html: bool = False) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.markdown", fake_markdown)

    from ui.bootstrap_theme import inject_bootstrap_theme

    inject_bootstrap_theme()
    assert len(captured) == 1
    assert "bootstrap@5.3.3" in captured[0]
    assert "bootstrap-icons" in captured[0]
    assert ".cp-shell" in captured[0]


def test_load_css_reads_file(monkeypatch):
    captured: list[str] = []

    def fake_markdown(body: str, unsafe_allow_html: bool = False) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.markdown", fake_markdown)

    from ui.theme import load_css

    load_css()
    assert len(captured) == 1
    assert "bootstrap@5.3.3" in captured[0]
    assert ".cp-metric-card" in captured[0]


def test_load_js_is_noop(monkeypatch):
    called = False

    def fake_html(body: str, height: int = 0, **kwargs) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("streamlit.components.v1.html", fake_html)

    from ui.theme import load_js

    load_js()
    assert called is False

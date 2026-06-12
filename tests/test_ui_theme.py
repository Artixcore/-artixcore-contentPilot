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


def test_app_css_has_no_javascript():
    css = (ROOT / "assets" / "styles" / "app.css").read_text(encoding="utf-8")
    assert "function " not in css
    assert "document." not in css
    assert "addEventListener" not in css
    assert "<script>" not in css


def test_app_js_has_no_css():
    js = (ROOT / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    assert "@import" not in js
    assert "font-family:" not in js
    assert "border-radius:" not in js
    assert ":root" not in js


def test_no_partial_html_wrappers_in_ui():
    """UI modules must not open/close divs across separate st.markdown calls."""
    ui_dir = ROOT / "ui"
    offenders: list[str] = []
    for path in ui_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "st.markdown('</div>" in text or 'st.markdown("</div>' in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"Partial HTML wrappers found: {offenders}"


def test_load_bootstrap_injects_cdn(monkeypatch):
    captured: list[str] = []

    def fake_markdown(body: str, unsafe_allow_html: bool = False) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.markdown", fake_markdown)

    from ui.bootstrap_theme import load_bootstrap

    load_bootstrap()
    assert len(captured) == 1
    assert "bootstrap@5.3.3" in captured[0]
    assert "bootstrap-icons" in captured[0]
    assert "function getShell" not in captured[0]


def test_load_css_reads_file(monkeypatch):
    captured: list[str] = []

    def fake_markdown(body: str, unsafe_allow_html: bool = False) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.markdown", fake_markdown)

    from ui.bootstrap_theme import load_css

    load_css()
    assert len(captured) == 1
    assert ".cp-metric-card" in captured[0]
    assert "function getShell" not in captured[0]


def test_load_js_uses_components_html(monkeypatch):
    captured: list[str] = []

    def fake_html(body: str, height: int = 0, **kwargs) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.components.v1.html", fake_html)

    from ui.bootstrap_theme import load_js

    load_js()
    assert len(captured) == 1
    assert "<script>" in captured[0]
    assert "data-cp-mobile-menu" in captured[0] or "DOMContentLoaded" in captured[0]


def test_init_theme_calls_all_loaders(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(
        "ui.bootstrap_theme.load_bootstrap",
        lambda: calls.append("bootstrap"),
    )
    monkeypatch.setattr(
        "ui.bootstrap_theme.load_css",
        lambda: calls.append("css"),
    )
    monkeypatch.setattr(
        "ui.bootstrap_theme.load_js",
        lambda: calls.append("js"),
    )

    from ui.bootstrap_theme import init_theme

    init_theme()
    assert calls == ["bootstrap", "css", "js"]

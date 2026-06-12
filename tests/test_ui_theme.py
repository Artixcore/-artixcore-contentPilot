"""UI theme and asset smoke tests."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_app_css_exists_and_has_core_classes():
    css_path = ROOT / "assets" / "styles" / "app.css"
    assert css_path.is_file(), "assets/styles/app.css must exist"
    css = css_path.read_text(encoding="utf-8")
    assert ".cp-metric-card" in css
    assert ".cp-topbar" in css
    assert ".cp-shell" not in css
    assert ".cp-icon-rail" not in css
    assert ".cp-bg" not in css
    assert '[data-testid="stSidebar"]' in css
    assert '[data-testid="stSidebar"]' in css
    assert 'stSidebar"] {\n  display: none' not in css
    assert ".block-container" in css
    assert "radial-gradient" not in css


def test_app_css_has_no_javascript():
    css = (ROOT / "assets" / "styles" / "app.css").read_text(encoding="utf-8")
    assert "function " not in css
    assert "document." not in css
    assert "addEventListener" not in css
    assert "<script>" not in css


def test_app_js_is_disabled():
    js = (ROOT / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    assert "addEventListener" not in js
    assert "DOMContentLoaded" not in js


def test_no_partial_html_wrappers_in_ui():
    """UI modules must not open/close divs across separate st.markdown calls."""
    ui_dir = ROOT / "ui"
    offenders: list[str] = []
    for path in ui_dir.glob("*.py"):
        if path.name.startswith("bootstrap_"):
            continue
        text = path.read_text(encoding="utf-8")
        if "st.markdown('</div>" in text or 'st.markdown("</div>' in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"Partial HTML wrappers found: {offenders}"


def test_load_bootstrap_injects_cdn(monkeypatch):
    captured: list[str] = []

    def fake_markdown(body: str, unsafe_allow_html: bool = False) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.markdown", fake_markdown)

    from ui.theme import load_bootstrap

    load_bootstrap()
    assert len(captured) == 1
    assert "bootstrap@5.3.3" in captured[0]
    assert "bootstrap-icons" in captured[0]
    assert "<script>" not in captured[0]


def test_load_css_reads_file(monkeypatch):
    captured: list[str] = []

    def fake_markdown(body: str, unsafe_allow_html: bool = False) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.markdown", fake_markdown)

    from ui.theme import load_css

    load_css()
    assert len(captured) == 1
    assert ".cp-metric-card" in captured[0]


def test_init_theme_calls_loaders(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(
        "ui.theme.load_bootstrap",
        lambda: calls.append("bootstrap"),
    )
    monkeypatch.setattr(
        "ui.theme.load_css",
        lambda: calls.append("css"),
    )

    from ui.theme import init_theme

    init_theme()
    assert calls == ["bootstrap", "css"]

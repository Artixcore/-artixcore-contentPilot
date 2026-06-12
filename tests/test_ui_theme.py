"""UI theme and asset smoke tests."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_app_css_exists_and_has_shell_classes():
    css_path = ROOT / "assets" / "styles" / "app.css"
    assert css_path.is_file(), "assets/styles/app.css must exist"
    css = css_path.read_text(encoding="utf-8")
    assert ".cp-page-bg" in css
    assert ".cp-shell-rail" in css
    assert ".cp-upgrade-btn" in css
    assert ".cp-dashboard-grid" in css
    assert ".cp-metric-card" in css


def test_app_js_exists():
    js_path = ROOT / "assets" / "js" / "app.js"
    assert js_path.is_file(), "assets/js/app.js must exist"


def test_load_css_reads_file(monkeypatch):
    captured: list[str] = []

    def fake_markdown(body: str, unsafe_allow_html: bool = False) -> None:
        captured.append(body)

    monkeypatch.setattr("streamlit.markdown", fake_markdown)

    from ui.theme import load_css

    load_css()
    assert len(captured) == 1
    assert captured[0].startswith("<style>")
    assert ".cp-page-bg" in captured[0]


def test_load_js_reads_file(monkeypatch):
    called: list[str] = []

    def fake_html(body: str, height: int = 0, **kwargs) -> None:
        called.append(body)

    monkeypatch.setattr("streamlit.components.v1.html", fake_html)

    from ui.theme import load_js

    load_js()
    assert len(called) == 1
    assert "<script>" in called[0]

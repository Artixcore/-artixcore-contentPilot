"""Bootstrap 5 CDN theme injection and Streamlit chrome reset."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"

BOOTSTRAP_CDN = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
"""


def _read_asset(relative: str) -> str:
    path = _ASSETS_ROOT / relative
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_bootstrap() -> None:
    """Inject Bootstrap 5 CDN CSS, Icons, and JS bundle."""
    st.markdown(BOOTSTRAP_CDN, unsafe_allow_html=True)


def load_css() -> None:
    """Load local app stylesheet."""
    css_path = _ASSETS_ROOT / "styles" / "app.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def load_js() -> None:
    """Load local app JavaScript via components.html (not st.markdown)."""
    js_path = _ASSETS_ROOT / "js" / "app.js"
    if js_path.exists():
        components.html(f"<script>{js_path.read_text(encoding='utf-8')}</script>", height=0)


def init_theme() -> None:
    """Inject Bootstrap CDN, custom CSS, and app JS once per run."""
    load_bootstrap()
    load_css()
    load_js()


def inject_bootstrap_theme() -> None:
    """Backward-compatible alias for init_theme()."""
    init_theme()

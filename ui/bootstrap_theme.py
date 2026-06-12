"""Bootstrap 5 CDN theme injection and Streamlit chrome reset."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"

BOOTSTRAP_CDN = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
"""

STREAMLIT_RESET_CSS = """
[data-testid="stSidebar"] {
  display: none !important;
}

[data-testid="collapsedControl"] {
  display: none !important;
}

[data-testid="stHeader"] {
  display: none !important;
}

#MainMenu, footer {
  visibility: hidden !important;
}

.block-container {
  max-width: 100% !important;
  padding: 0 !important;
}

[data-testid="stAppViewContainer"] {
  background: radial-gradient(circle at center, #f5bc6b 0%, #d99043 46%, #c9792b 100%) !important;
}

.stApp {
  background: transparent !important;
}
"""


def _read_asset(relative: str) -> str:
    return (_ASSETS_ROOT / relative).read_text(encoding="utf-8")


def inject_bootstrap_theme() -> None:
    """Inject Bootstrap CDN, custom CSS, and app JS once per run."""
    app_css = _read_asset("styles/app.css")
    app_js = _read_asset("js/app.js")
    payload = (
        BOOTSTRAP_CDN
        + f"<style>{STREAMLIT_RESET_CSS}\n{app_css}</style>"
        + f"<script>{app_js}</script>"
    )
    st.markdown(payload, unsafe_allow_html=True)


def load_css() -> None:
    """Backward-compatible alias."""
    inject_bootstrap_theme()


def load_js() -> None:
    """JS is bundled inside inject_bootstrap_theme()."""
    return

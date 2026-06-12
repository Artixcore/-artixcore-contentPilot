"""Artixcore ContentPilot design tokens and global CSS loading."""

from __future__ import annotations

from pathlib import Path

from ui.bootstrap_theme import init_theme, load_css, load_js

# Brand tokens (used by components for inline HTML)
PRIMARY = "#D97706"
PRIMARY_DARK = "#B45309"
SECONDARY = "#F59E0B"
BG_WHITE = "#FFFFFF"
BG_PANEL = "#F9FAFB"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"
TEXT_MUTED = "#9CA3AF"
BORDER = "#E5E7EB"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
INFO = "#2563EB"

RADIUS_SM = "10px"
RADIUS_MD = "14px"
RADIUS_LG = "18px"
RADIUS_XL = "24px"

SHADOW_SOFT = "0 8px 24px rgba(15, 23, 42, 0.08)"
SHADOW_CARD = "0 18px 50px rgba(15, 23, 42, 0.10)"

FONT_STACK = (
    'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, '
    '"Segoe UI", Roboto, sans-serif'
)

_ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"


def inject_theme() -> None:
    """Backward-compatible alias for init_theme()."""
    init_theme()

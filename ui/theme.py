"""Artixcore ContentPilot design tokens and global CSS."""

import streamlit as st

# Brand tokens
PRIMARY = "#D97706"
PRIMARY_DARK = "#B45309"
SECONDARY = "#F59E0B"
BG_WHITE = "#FFFFFF"
BG_PANEL = "#F9FAFB"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"
TEXT_MUTED = "#9CA3AF"
BORDER = "#E5E7EB"
SUCCESS = "#059669"
WARNING = "#D97706"
DANGER = "#DC2626"
INFO = "#2563EB"

RADIUS_SM = "12px"
RADIUS_MD = "16px"
RADIUS_LG = "20px"
RADIUS_XL = "24px"

SHADOW_SOFT = "0 4px 24px rgba(17, 24, 39, 0.06)"
SHADOW_CARD = "0 1px 3px rgba(17, 24, 39, 0.06), 0 4px 16px rgba(217, 119, 6, 0.04)"

FONT_STACK = (
    'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, '
    '"Segoe UI", Roboto, sans-serif'
)


def inject_theme() -> None:
    """Inject global CSS for the premium dashboard shell."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {{
            --cp-primary: {PRIMARY};
            --cp-primary-dark: {PRIMARY_DARK};
            --cp-secondary: {SECONDARY};
            --cp-bg: {BG_WHITE};
            --cp-panel: {BG_PANEL};
            --cp-text: {TEXT_PRIMARY};
            --cp-text-secondary: {TEXT_SECONDARY};
            --cp-text-muted: {TEXT_MUTED};
            --cp-border: {BORDER};
            --cp-radius: {RADIUS_MD};
            --cp-shadow: {SHADOW_SOFT};
            --cp-font: {FONT_STACK};
        }}

        /* Hide Streamlit chrome */
        #MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none !important; }}
        .stApp {{
            background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 25%, #FED7AA 55%, #FFEDD5 100%) !important;
            font-family: var(--cp-font) !important;
        }}
        .block-container {{
            padding: 0.75rem 1rem 1rem !important;
            max-width: 100% !important;
        }}
        @media (max-width: 640px) {{
            .block-container {{ padding: 0.25rem 0.5rem 4.5rem !important; }}
        }}

        /* App shell */
        .cp-outer {{ min-height: calc(100vh - 1.5rem); display: flex; justify-content: center; padding: 0.5rem; }}
        .cp-app-container {{
            width: 94vw; max-width: 1680px; min-height: 88vh;
            background: {BG_WHITE}; border-radius: {RADIUS_XL};
            border: 1px solid rgba(255,255,255,0.6); box-shadow: {SHADOW_SOFT};
            display: flex; flex-direction: column; overflow: hidden;
        }}
        @media (max-width: 640px) {{
            .cp-outer {{ padding: 0; min-height: 100vh; }}
            .cp-app-container {{ width: 100vw; min-height: 100vh; border-radius: 0; border: none; }}
        }}

        .cp-shell-row {{ display: flex; flex: 1; min-height: 0; }}
        .cp-icon-rail {{
            width: 64px; min-width: 64px; background: {BG_WHITE};
            border-right: 1px solid {BORDER}; display: flex; flex-direction: column;
            align-items: center; padding: 12px 0; gap: 4px;
        }}
        .cp-sidebar {{
            width: 280px; min-width: 280px; background: {BG_WHITE};
            border-right: 1px solid {BORDER}; display: flex; flex-direction: column;
            padding: 20px 16px; overflow-y: auto;
        }}
        .cp-sidebar.collapsed {{ display: none; }}
        .cp-main {{ flex: 1; display: flex; flex-direction: column; min-width: 0; background: {BG_WHITE}; }}
        .cp-topbar {{
            height: 72px; min-height: 72px; border-bottom: 1px solid {BORDER};
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; background: {BG_WHITE};
        }}
        .cp-content-area {{ flex: 1; overflow-y: auto; padding: 24px; }}
        @media (max-width: 1024px) {{
            .cp-sidebar {{ position: absolute; z-index: 100; height: calc(100% - 72px);
                top: 72px; left: 64px; box-shadow: {SHADOW_SOFT}; }}
            .cp-sidebar.collapsed {{ display: none; }}
        }}
        @media (max-width: 640px) {{
            .cp-icon-rail {{
                position: fixed; bottom: 0; left: 0; right: 0; width: 100%;
                min-width: 100%; height: 64px; flex-direction: row;
                justify-content: space-around; border-right: none;
                border-top: 1px solid {BORDER}; z-index: 200; padding: 0 8px;
            }}
            .cp-sidebar {{ left: 0; width: 100%; min-width: 100%; }}
            .cp-content-area {{ padding: 16px; }}
            .cp-topbar {{ padding: 0 12px; height: 64px; min-height: 64px; }}
        }}

        /* Typography helpers */
        .cp-page-title {{ font-size: 1.5rem; font-weight: 700; color: {TEXT_PRIMARY}; margin: 0 0 4px 0; }}
        .cp-page-subtitle {{ font-size: 0.875rem; color: {TEXT_SECONDARY}; margin: 0 0 20px 0; }}
        .cp-section-title {{ font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.05em; color: {TEXT_MUTED}; margin: 16px 0 8px 0; }}

        /* Cards */
        .cp-card {{
            background: {BG_WHITE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD};
            padding: 20px; margin-bottom: 16px; box-shadow: {SHADOW_CARD};
        }}
        .cp-card-panel {{ background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}; padding: 16px; }}
        .cp-metric-card {{
            background: {BG_WHITE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD};
            padding: 16px 20px; box-shadow: {SHADOW_CARD};
        }}
        .cp-metric-label {{ font-size: 0.75rem; color: {TEXT_SECONDARY}; font-weight: 500; margin-bottom: 4px; }}
        .cp-metric-value {{ font-size: 1.75rem; font-weight: 700; color: {TEXT_PRIMARY}; }}
        .cp-metric-icon {{ color: {PRIMARY}; margin-bottom: 8px; }}

        /* Badges */
        .cp-badge {{
            display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 0.75rem; font-weight: 500;
        }}
        .cp-badge-success {{ background: #D1FAE5; color: #065F46; }}
        .cp-badge-warning {{ background: #FEF3C7; color: #92400E; }}
        .cp-badge-danger {{ background: #FEE2E2; color: #991B1B; }}
        .cp-badge-info {{ background: #DBEAFE; color: #1E40AF; }}
        .cp-badge-muted {{ background: {BG_PANEL}; color: {TEXT_SECONDARY}; }}

        /* Nav items (HTML decorative) */
        .cp-nav-item {{
            display: flex; align-items: center; gap: 10px; padding: 8px 12px;
            border-radius: {RADIUS_SM}; color: {TEXT_SECONDARY}; font-size: 0.875rem;
            cursor: default; margin-bottom: 2px;
        }}
        .cp-nav-item.active {{ background: #FFF7ED; color: {PRIMARY}; font-weight: 600; }}
        .cp-nav-item:hover {{ background: {BG_PANEL}; }}
        .cp-workspace-item {{ padding-left: 28px; font-size: 0.8125rem; }}

        /* Upgrade card */
        .cp-upgrade-card {{
            background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
            border: 1px solid #FED7AA; border-radius: {RADIUS_MD};
            padding: 16px; margin-top: auto;
        }}
        .cp-upgrade-title {{ font-weight: 600; color: {TEXT_PRIMARY}; font-size: 0.875rem; margin-bottom: 6px; }}
        .cp-upgrade-text {{ font-size: 0.75rem; color: {TEXT_SECONDARY}; line-height: 1.4; margin-bottom: 12px; }}

        /* Chat bubbles */
        .cp-chat-user {{
            background: #FFF7ED; border: 1px solid #FED7AA; border-radius: {RADIUS_MD};
            padding: 14px 18px; margin: 8px 0 8px 15%; max-width: 85%;
        }}
        .cp-chat-ai {{
            background: {BG_WHITE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD};
            padding: 14px 18px; margin: 8px 15% 8px 0; max-width: 85%;
            box-shadow: {SHADOW_CARD};
        }}
        .cp-chat-meta {{ font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 8px;
            border-top: 1px solid {BORDER}; padding-top: 8px; }}
        .cp-date-divider {{
            text-align: center; font-size: 0.75rem; color: {TEXT_MUTED};
            margin: 20px 0; font-weight: 500;
        }}

        /* Template cards */
        .cp-template-card {{
            background: {BG_WHITE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD};
            padding: 16px; display: flex; align-items: flex-start; gap: 12px;
            transition: border-color 0.15s, box-shadow 0.15s;
        }}
        .cp-template-card:hover {{ border-color: {PRIMARY}; box-shadow: {SHADOW_CARD}; }}
        .cp-template-text {{ flex: 1; font-size: 0.875rem; color: {TEXT_PRIMARY}; line-height: 1.4; }}

        /* Welcome hero */
        .cp-welcome-hero {{ text-align: center; padding: 40px 20px 24px; }}
        .cp-logo-mark {{
            width: 56px; height: 56px; border-radius: 50%;
            background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
            display: inline-flex; align-items: center; justify-content: center;
            color: white; font-weight: 700; font-size: 1.25rem; margin-bottom: 20px;
        }}
        .cp-welcome-title {{ font-size: 1.75rem; font-weight: 700; color: {TEXT_PRIMARY}; margin-bottom: 8px; }}
        .cp-welcome-sub {{ font-size: 1rem; color: {TEXT_SECONDARY}; margin-bottom: 4px; }}
        .cp-welcome-sub2 {{ font-size: 0.875rem; color: {TEXT_MUTED}; }}

        /* Grid */
        .cp-grid {{ display: grid; gap: 16px; }}
        .cp-grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .cp-grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
        .cp-grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
        .cp-grid-5 {{ grid-template-columns: repeat(5, 1fr); }}
        .cp-grid-6 {{ grid-template-columns: repeat(6, 1fr); }}
        @media (max-width: 1024px) {{
            .cp-grid-6, .cp-grid-5, .cp-grid-4 {{ grid-template-columns: repeat(3, 1fr); }}
        }}
        @media (max-width: 640px) {{
            .cp-grid-6, .cp-grid-5, .cp-grid-4, .cp-grid-3, .cp-grid-2 {{ grid-template-columns: 1fr; }}
        }}

        /* Table cards (mobile) */
        .cp-table-card {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM};
            padding: 12px 16px; margin-bottom: 8px; background: {BG_WHITE}; }}
        .cp-table-card-row {{ display: flex; justify-content: space-between; font-size: 0.8125rem;
            padding: 4px 0; border-bottom: 1px solid {BG_PANEL}; }}
        .cp-table-card-row:last-child {{ border-bottom: none; }}
        .cp-table-card-label {{ color: {TEXT_MUTED}; }}
        .cp-table-card-value {{ color: {TEXT_PRIMARY}; font-weight: 500; text-align: right; }}

        /* Streamlit widget overrides */
        .stButton > button {{
            border-radius: 999px !important; font-family: var(--cp-font) !important;
            font-weight: 500 !important; transition: all 0.15s !important;
            min-height: 44px !important;
        }}
        .stButton > button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {{
            background: {PRIMARY} !important; border-color: {PRIMARY} !important; color: white !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {PRIMARY_DARK} !important; border-color: {PRIMARY_DARK} !important;
        }}
        .stButton > button[kind="secondary"] {{
            background: {BG_WHITE} !important; border: 1px solid {BORDER} !important; color: {TEXT_PRIMARY} !important;
        }}
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
            border-radius: {RADIUS_SM} !important; border-color: {BORDER} !important;
            font-family: var(--cp-font) !important;
        }}
        div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {{
            border-color: {PRIMARY} !important; box-shadow: 0 0 0 2px rgba(217,119,6,0.15) !important;
        }}
        .stMetric {{ background: {BG_WHITE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD};
            padding: 16px; box-shadow: {SHADOW_CARD}; }}

        /* Nav button strip (invisible overlay pattern) */
        .cp-nav-btn-wrap {{ margin: 0; padding: 0; }}
        .cp-nav-btn-wrap .stButton > button {{
            width: 44px !important; height: 44px !important; min-height: 44px !important;
            padding: 0 !important; border-radius: {RADIUS_SM} !important;
            background: transparent !important; border: none !important; color: {TEXT_SECONDARY} !important;
            font-size: 1.1rem !important;
        }}
        .cp-nav-btn-wrap.active .stButton > button {{
            background: #FFF7ED !important; color: {PRIMARY} !important;
        }}
        .cp-sidebar-nav .stButton > button {{
            width: 100% !important; text-align: left !important; justify-content: flex-start !important;
            border-radius: {RADIUS_SM} !important; background: transparent !important;
            border: none !important; color: {TEXT_SECONDARY} !important; font-size: 0.875rem !important;
            padding: 8px 12px !important; min-height: 36px !important;
        }}
        .cp-sidebar-nav.active .stButton > button {{
            background: #FFF7ED !important; color: {PRIMARY} !important; font-weight: 600 !important;
        }}
        .cp-topbar-btn .stButton > button {{
            min-height: 40px !important; border-radius: {RADIUS_SM} !important;
            font-size: 0.8125rem !important;
        }}
        .cp-icon-btn .stButton > button {{
            width: 40px !important; min-width: 40px !important; height: 40px !important;
            min-height: 40px !important; padding: 0 !important; border-radius: {RADIUS_SM} !important;
            background: {BG_PANEL} !important; border: 1px solid {BORDER} !important;
        }}

        /* Sticky chat input area */
        .cp-chat-input-area {{
            position: sticky; bottom: 0; background: {BG_WHITE};
            border-top: 1px solid {BORDER}; padding: 16px 0 0; margin-top: 16px;
        }}

        /* Platform selector cards */
        .cp-platform-card {{
            border: 1px solid {BORDER}; border-radius: {RADIUS_MD}; padding: 16px;
            text-align: center; cursor: pointer; transition: all 0.15s;
        }}
        .cp-platform-card.selected {{ border-color: {PRIMARY}; background: #FFF7ED; }}
        .cp-platform-card:hover {{ border-color: {PRIMARY}; }}

        /* Alert banners */
        .cp-alert {{ padding: 12px 16px; border-radius: {RADIUS_SM}; margin-bottom: 16px; font-size: 0.875rem; }}
        .cp-alert-error {{ background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }}
        .cp-alert-warning {{ background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; }}
        .cp-alert-info {{ background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; }}
        .cp-alert-success {{ background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; }}

        /* Inbox split */
        .cp-inbox-layout {{ display: grid; grid-template-columns: 320px 1fr; gap: 16px; min-height: 500px; }}
        @media (max-width: 768px) {{
            .cp-inbox-layout {{ grid-template-columns: 1fr; }}
        }}
        .cp-inbox-list {{ border: 1px solid {BORDER}; border-radius: {RADIUS_MD}; overflow-y: auto; max-height: 600px; }}
        .cp-inbox-item {{ padding: 12px 16px; border-bottom: 1px solid {BORDER}; cursor: pointer; }}
        .cp-inbox-item.active {{ background: #FFF7ED; border-left: 3px solid {PRIMARY}; }}
        .cp-inbox-item:hover {{ background: {BG_PANEL}; }}

        /* Hide empty streamlit spacing in shell */
        .cp-shell-marker {{ display: none; }}

        /* Shell column styling */
        [data-testid="stHorizontalBlock"]:has(.cp-shell-rail) {{
            gap: 0 !important; align-items: stretch !important;
        }}
        .cp-shell-rail [data-testid="stVerticalBlock"] {{
            background: {BG_WHITE}; border-right: 1px solid {BORDER};
            padding: 8px 4px !important; min-height: 85vh;
        }}
        .cp-shell-sidebar [data-testid="stVerticalBlock"] {{
            background: {BG_WHITE}; border-right: 1px solid {BORDER};
            padding: 12px 8px !important; min-height: 85vh;
        }}
        .cp-shell-main [data-testid="stVerticalBlock"] {{
            background: {BG_WHITE}; min-height: 85vh;
        }}
        @media (max-width: 640px) {{
            .cp-shell-rail [data-testid="stVerticalBlock"] {{
                position: fixed; bottom: 0; left: 0; right: 0;
                min-height: auto !important; height: 64px; flex-direction: row !important;
                border-right: none; border-top: 1px solid {BORDER}; z-index: 200;
            }}
            .cp-shell-rail [data-testid="stHorizontalBlock"] {{
                flex-direction: row !important; justify-content: space-around !important;
            }}
        }}

        /* Dataframe mobile fallback hint */
        @media (max-width: 640px) {{
            [data-testid="stDataFrame"] {{ font-size: 0.75rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

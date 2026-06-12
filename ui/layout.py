"""Native Streamlit sidebar and topbar layout."""

from __future__ import annotations

import streamlit as st

from ui.navigation import NAV_LABELS, SIDEBAR_WORKSPACES

NAV_PAGES = NAV_LABELS


def render_sidebar() -> str:
    """Render native Streamlit sidebar and return selected page label."""
    with st.sidebar:
        st.title("Artixcore Pilot")
        st.caption("ContentPilot")

        if st.button("+ New Content", use_container_width=True, key="nav_new_content"):
            st.session_state["page"] = "Create Post"
            st.rerun()

        if st.button("Import", use_container_width=True, key="nav_import"):
            st.info("Import feature coming soon.")

        st.text_input("Search", placeholder="Search...", label_visibility="collapsed", key="sidebar_search")

        default_index = 0
        if "page_radio" in st.session_state and st.session_state["page_radio"] in NAV_PAGES:
            default_index = NAV_PAGES.index(st.session_state["page_radio"])

        forced = st.session_state.pop("page", None)
        if forced and forced in NAV_PAGES:
            default_index = NAV_PAGES.index(forced)
            st.session_state["page_radio"] = forced

        selected = st.radio(
            "Navigation",
            NAV_PAGES,
            index=default_index,
            key="page_radio",
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.caption("Works / Projects")
        for ws in SIDEBAR_WORKSPACES[:3]:
            st.button(ws, use_container_width=True, key=f"workspace_{ws}")

        st.markdown("---")
        st.info(
            "Premium Plan: Unlock advanced automation, team approval, analytics, and cloud publishing."
        )

    return selected


def render_topbar() -> None:
    st.markdown(
        """
    <div class="cp-topbar">
      <div class="cp-topbar-title">Artixcore ContentPilot</div>
      <div class="cp-topbar-actions">
        <span class="cp-badge cp-badge-warning">Upgrade Plan</span>
        <span class="cp-badge cp-badge-success">System Ready</span>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

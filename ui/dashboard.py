"""Dashboard page."""

import streamlit as st
from sqlalchemy.orm import Session

from core.cache import get_or_set
from core.chat_database import count_open_conversations
from core.health import format_health_for_display, get_overall_status
from core.models import Post
from core.publishing import get_publisher_statuses
from core.router import ProviderRouter
from core.training_data import get_training_stats
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.components import (
    render_alert,
    render_connector_status,
    render_data_table_or_cards,
    render_metrics_grid,
    render_page_header,
    render_section_header,
    render_status_badge,
)


def render(session: Session) -> None:
    render_page_header("Dashboard", "Overview of your content pipeline and provider status.")

    def _dashboard_stats():
        return {
            "total": session.query(Post).count(),
            "pending": session.query(Post).filter(Post.status == "pending_approval").count(),
            "published": session.query(Post).filter(Post.status == "published").count(),
            "chat_convos": count_open_conversations(session),
            "training_stats": get_training_stats(session),
        }

    stats = get_or_set("dashboard_stats", _dashboard_stats)
    total = stats["total"]
    pending = stats["pending"]
    published = stats["published"]
    chat_convos = stats["chat_convos"]
    training_stats = stats["training_stats"]

    render_metrics_grid([
        ("Total Posts", total, "📝"),
        ("Pending Approval", pending, "⏳"),
        ("Published", published, "✓"),
        ("Chat Conversations", chat_convos, "💬"),
        ("AI Training Examples", training_stats["total"], "◎"),
    ])

    router = ProviderRouter(session=session)
    availability = get_or_set("provider_status", lambda: router.get_availability_status())
    if not availability.get("openai") and not availability.get("anthropic"):
        render_alert(PROVIDER_UNAVAILABLE_MSG, "error")

    render_section_header("Provider Status")
    pc1, pc2 = st.columns(2)
    with pc1:
        render_connector_status("OpenAI", bool(availability.get("openai")))
    with pc2:
        render_connector_status("Anthropic", bool(availability.get("anthropic")))

    render_section_header("System Health")
    overall = get_overall_status()
    overall_kind = {"healthy": "success", "warning": "warning", "error": "danger"}.get(overall, "muted")
    st.markdown(
        f'<p>Overall status: {render_status_badge(overall.title(), overall_kind)}</p>',
        unsafe_allow_html=True,
    )
    health_checks = format_health_for_display()
    hcols = st.columns(3)
    for i, check in enumerate(health_checks):
        kind = {"healthy": "success", "warning": "warning", "error": "danger"}.get(check["status"], "muted")
        with hcols[i % 3]:
            st.markdown(
                f'<div class="cp-card" style="padding:10px;margin-bottom:8px;">'
                f'{render_status_badge(check["name"].replace("_", " ").title(), kind)}'
                f'<p style="font-size:0.75rem;margin:6px 0 0;color:#6B7280;">{check["message"]}</p></div>',
                unsafe_allow_html=True,
            )

    render_section_header("Connector Health")
    pub_statuses = get_or_set("connector_status", get_publisher_statuses)
    pub_labels = {
        "linkedin": "LinkedIn",
        "twitter": "X / Twitter",
        "facebook": "Facebook",
        "instagram": "Instagram",
        "website_blog": "Website",
    }
    ch_cols = st.columns(3)
    for i, (key, label) in enumerate(pub_labels.items()):
        with ch_cols[i % 3]:
            render_connector_status(label, pub_statuses.get(key, False))

    render_section_header("Recent Activity")
    posts = session.query(Post).order_by(Post.created_at.desc()).limit(20).all()
    if posts:
        rows = [
            {
                "id": p.id,
                "platform": p.platform,
                "topic": p.topic[:50],
                "status": p.status,
                "provider": p.provider_used or "-",
                "created": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            }
            for p in posts
        ]
        card_view = st.toggle("Card view (mobile-friendly)", value=False, key="dash_card_view")
        render_data_table_or_cards(
            rows,
            [
                ("id", "ID"),
                ("platform", "Platform"),
                ("topic", "Topic"),
                ("status", "Status"),
                ("provider", "Provider"),
                ("created", "Created"),
            ],
            use_dataframe=not card_view,
        )
    else:
        st.markdown(
            '<p style="color:#9CA3AF;font-size:0.875rem;">No posts yet. Create your first post from Create Post or AI Workspace.</p>',
            unsafe_allow_html=True,
        )

    pending_posts = session.query(Post).filter(Post.status == "pending_approval").limit(5).all()
    if pending_posts:
        render_section_header("Pending Tasks")
        for p in pending_posts:
            badge = render_status_badge(p.status.replace("_", " ").title(), "pending")
            st.markdown(
                f'<div class="cp-card" style="padding:12px 16px;margin-bottom:8px;">'
                f'<strong>#{p.id}</strong> {p.platform.title()} — {p.topic[:60]} {badge}</div>',
                unsafe_allow_html=True,
            )

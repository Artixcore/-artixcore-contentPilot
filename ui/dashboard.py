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
    render_data_table_or_cards,
    render_health_card,
    render_metric_card,
    render_page_header,
    render_provider_card,
    render_queue_card,
    render_section_title,
    render_status_badge,
)


def render(session: Session) -> None:
    render_page_header(
        "Dashboard",
        "Overview of your content pipeline, chatbot activity, publishing connectors, and system health.",
    )

    st.write("")

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

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("Total Posts", total, "📝")
    with col2:
        render_metric_card("Pending Approval", pending, "⏳")
    with col3:
        render_metric_card("Published", published, "✅")
    with col4:
        render_metric_card("Chat Conversations", chat_convos, "💬")
    with col5:
        render_metric_card("AI Training Examples", training_stats["total"], "🎯")

    router = ProviderRouter(session=session)
    availability = get_or_set("provider_status", lambda: router.get_availability_status())
    if not availability.get("openai") and not availability.get("anthropic"):
        render_alert(PROVIDER_UNAVAILABLE_MSG, "error")

    st.write("")
    render_section_title("Provider Status")

    p1, p2 = st.columns(2)
    with p1:
        render_provider_card("OpenAI", bool(availability.get("openai")), "OpenAI content generation provider.")
    with p2:
        render_provider_card("Anthropic", bool(availability.get("anthropic")), "Anthropic content generation provider.")

    st.write("")
    render_section_title("System Health")

    overall = get_overall_status()
    overall_kind = {"healthy": "success", "warning": "warning", "error": "danger"}.get(overall, "muted")
    st.markdown(
        f'<p style="margin-bottom:12px;">Overall: {render_status_badge(overall.title(), overall_kind)}</p>',
        unsafe_allow_html=True,
    )

    health_checks = format_health_for_display()
    for row_start in range(0, len(health_checks), 3):
        hcols = st.columns(3)
        for i, check in enumerate(health_checks[row_start : row_start + 3]):
            with hcols[i]:
                render_health_card(
                    check["name"].replace("_", " ").title(),
                    check["status"],
                    check["message"],
                )

    st.write("")
    render_section_title("Connector Health")

    pub_statuses = get_or_set("connector_status", get_publisher_statuses)
    pub_labels = {
        "linkedin": "LinkedIn",
        "twitter": "X / Twitter",
        "facebook": "Facebook",
        "instagram": "Instagram",
        "website_blog": "Website",
    }
    pub_items = list(pub_labels.items())
    for row_start in range(0, len(pub_items), 3):
        ch_cols = st.columns(3)
        for i, (key, label) in enumerate(pub_items[row_start : row_start + 3]):
            with ch_cols[i]:
                render_provider_card(label, pub_statuses.get(key, False))

    st.write("")
    render_section_title("Recent Activity")

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
        st.info("No posts yet. Create your first post from Create Post or AI Workspace.")

    pending_posts = session.query(Post).filter(Post.status == "pending_approval").limit(5).all()
    if pending_posts:
        st.write("")
        render_section_title("Pending Tasks")
        for p in pending_posts:
            badge = render_status_badge(p.status.replace("_", " ").title(), "pending")
            render_queue_card(
                f"#{p.id} {p.platform.title()}",
                badge,
                p.topic[:60],
                "Awaiting approval",
            )

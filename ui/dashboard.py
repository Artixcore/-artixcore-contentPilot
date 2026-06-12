"""Dashboard page."""

import pandas as pd
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
    badge_html,
    page_header,
    queue_card,
    section_title,
    status_card,
    metric_card,
    alert_card,
)


def render_dashboard(session: Session) -> None:
    def _dashboard_stats():
        return {
            "total": session.query(Post).count(),
            "pending": session.query(Post).filter(Post.status == "pending_approval").count(),
            "published": session.query(Post).filter(Post.status == "published").count(),
            "chat_convos": count_open_conversations(session),
            "training_stats": get_training_stats(session),
        }

    stats = get_or_set("dashboard_stats", _dashboard_stats)
    router = ProviderRouter(session=session)
    availability = get_or_set("provider_status", lambda: router.get_availability_status())
    health_checks = format_health_for_display()
    pub_statuses = get_or_set("connector_status", get_publisher_statuses)
    pending_posts = session.query(Post).filter(Post.status == "pending_approval").limit(5).all()

    page_header(
        "Dashboard",
        "Overview of your content pipeline, chatbot activity, publishing connectors, and system health.",
    )

    if not availability.get("openai") and not availability.get("anthropic"):
        alert_card(PROVIDER_UNAVAILABLE_MSG, "error")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Total Posts", stats["total"], "📝")
    with c2:
        metric_card("Pending Approval", stats["pending"], "⏳")
    with c3:
        metric_card("Published", stats["published"], "✅")
    with c4:
        metric_card("Chat Conversations", stats["chat_convos"], "💬")
    with c5:
        metric_card("AI Training Examples", stats["training_stats"]["total"], "🎯")

    section_title("Provider Status")
    p1, p2 = st.columns(2)
    with p1:
        status_card(
            "OpenAI",
            "OpenAI configured." if availability.get("openai") else "OpenAI API key missing.",
            "success" if availability.get("openai") else "warning",
        )
    with p2:
        status_card(
            "Anthropic",
            "Anthropic configured." if availability.get("anthropic") else "Anthropic API key missing.",
            "success" if availability.get("anthropic") else "warning",
        )

    section_title("System Health")
    overall = get_overall_status()
    overall_kind = {"healthy": "success", "warning": "warning", "error": "danger"}.get(overall, "warning")
    st.markdown(f"Overall: {badge_html(overall.title(), overall_kind)}", unsafe_allow_html=True)

    for i in range(0, len(health_checks), 3):
        row = health_checks[i : i + 3]
        cols = st.columns(3)
        for col, check in zip(cols, row):
            with col:
                status_card(
                    check["name"].replace("_", " ").title(),
                    check["message"],
                    check["status"],
                )

    section_title("Connector Health")
    pub_labels = {
        "linkedin": "LinkedIn",
        "twitter": "X / Twitter",
        "facebook": "Facebook",
        "instagram": "Instagram",
        "website_blog": "Website",
    }
    keys = list(pub_labels.keys())
    for i in range(0, len(keys), 3):
        cols = st.columns(3)
        for col, key in zip(cols, keys[i : i + 3]):
            with col:
                configured = pub_statuses.get(key, False)
                status_card(
                    pub_labels[key],
                    "Connector configured." if configured else "Connector not configured.",
                    "success" if configured else "warning",
                )

    if pending_posts:
        section_title("Pending Tasks")
        for p in pending_posts:
            queue_card(
                f"#{p.id} {p.platform.title()}",
                badge_html(p.status.replace("_", " ").title(), "pending"),
                p.topic[:60],
                "Awaiting approval",
            )

    section_title("Recent Activity")
    posts = session.query(Post).order_by(Post.created_at.desc()).limit(20).all()
    if posts:
        df = pd.DataFrame(
            [
                {
                    "ID": p.id,
                    "Platform": p.platform,
                    "Topic": p.topic[:50],
                    "Status": p.status,
                    "Provider": p.provider_used or "-",
                    "Created": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
                }
                for p in posts
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No posts yet. Create your first post from Create Post or AI Workspace.")


def render(session: Session) -> None:
    render_dashboard(session)

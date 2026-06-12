"""Dashboard page."""

from sqlalchemy.orm import Session

from core.cache import get_or_set
from core.chat_database import count_open_conversations
from core.health import format_health_for_display, get_overall_status
from core.models import Post
from core.publishing import get_publisher_statuses
from core.router import ProviderRouter
from core.training_data import get_training_stats
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.bootstrap_components import (
    alert_html,
    badge,
    escape_html,
    health_card,
    page_header,
    queue_card,
    section_title,
)


def render_html(session: Session) -> str:
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

    total = stats["total"]
    pending = stats["pending"]
    published = stats["published"]
    chat_convos = stats["chat_convos"]
    training_total = stats["training_stats"]["total"]

    metrics = f"""
    <div class="row g-4 mb-2">
      <div class="col-12 col-sm-6 col-xl">
        <div class="card cp-metric-card border rounded-4 shadow-sm h-100">
          <div class="card-body">
            <div class="cp-metric-icon"><i class="bi bi-file-text"></i></div>
            <div class="cp-metric-label">Total Posts</div>
            <div class="cp-metric-value">{total}</div>
          </div>
        </div>
      </div>
      <div class="col-12 col-sm-6 col-xl">
        <div class="card cp-metric-card border rounded-4 shadow-sm h-100">
          <div class="card-body">
            <div class="cp-metric-icon"><i class="bi bi-hourglass-split"></i></div>
            <div class="cp-metric-label">Pending Approval</div>
            <div class="cp-metric-value">{pending}</div>
          </div>
        </div>
      </div>
      <div class="col-12 col-sm-6 col-xl">
        <div class="card cp-metric-card border rounded-4 shadow-sm h-100">
          <div class="card-body">
            <div class="cp-metric-icon"><i class="bi bi-check-circle"></i></div>
            <div class="cp-metric-label">Published</div>
            <div class="cp-metric-value">{published}</div>
          </div>
        </div>
      </div>
      <div class="col-12 col-sm-6 col-xl">
        <div class="card cp-metric-card border rounded-4 shadow-sm h-100">
          <div class="card-body">
            <div class="cp-metric-icon"><i class="bi bi-chat-dots"></i></div>
            <div class="cp-metric-label">Chat Conversations</div>
            <div class="cp-metric-value">{chat_convos}</div>
          </div>
        </div>
      </div>
      <div class="col-12 col-sm-6 col-xl">
        <div class="card cp-metric-card border rounded-4 shadow-sm h-100">
          <div class="card-body">
            <div class="cp-metric-icon"><i class="bi bi-bullseye"></i></div>
            <div class="cp-metric-label">AI Training Examples</div>
            <div class="cp-metric-value">{training_total}</div>
          </div>
        </div>
      </div>
    </div>
    """

    alert = ""
    if not availability.get("openai") and not availability.get("anthropic"):
        alert = alert_html(PROVIDER_UNAVAILABLE_MSG, "error")

    providers = f"""
    <div class="row g-4">
      <div class="col-12 col-md-6">
        <div class="card cp-status-card border rounded-4 shadow-sm h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start gap-2">
              <span class="fw-semibold">OpenAI</span>
              {badge("Configured" if availability.get("openai") else "Not Configured", "success" if availability.get("openai") else "warning")}
            </div>
            <p class="cp-card-subtitle mb-0 mt-2">OpenAI content generation provider.</p>
          </div>
        </div>
      </div>
      <div class="col-12 col-md-6">
        <div class="card cp-status-card border rounded-4 shadow-sm h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start gap-2">
              <span class="fw-semibold">Anthropic</span>
              {badge("Configured" if availability.get("anthropic") else "Not Configured", "success" if availability.get("anthropic") else "warning")}
            </div>
            <p class="cp-card-subtitle mb-0 mt-2">Anthropic content generation provider.</p>
          </div>
        </div>
      </div>
    </div>
    """

    overall = get_overall_status()
    overall_kind = {"healthy": "success", "warning": "warning", "error": "danger"}.get(overall, "muted")
    health_rows = "".join(
        health_card(c["name"].replace("_", " ").title(), c["status"], c["message"])
        for c in health_checks
    )

    pub_labels = {
        "linkedin": "LinkedIn",
        "twitter": "X / Twitter",
        "facebook": "Facebook",
        "instagram": "Instagram",
        "website_blog": "Website",
    }
    connector_cards = "".join(
        f'<div class="col-12 col-md-6 col-lg-4">'
        f'<div class="card cp-status-card border rounded-4 shadow-sm h-100"><div class="card-body">'
        f'<div class="d-flex justify-content-between align-items-start gap-2">'
        f'<span class="fw-semibold">{escape_html(label)}</span>'
        f'{badge("Configured" if pub_statuses.get(key, False) else "Missing", "success" if pub_statuses.get(key, False) else "warning")}'
        f"</div></div></div></div>"
        for key, label in pub_labels.items()
    )

    pending_html = ""
    if pending_posts:
        cards = ""
        for p in pending_posts:
            cards += queue_card(
                f"#{p.id} {p.platform.title()}",
                badge(p.status.replace("_", " ").title(), "pending"),
                p.topic[:60],
                "Awaiting approval",
            )
        pending_html = section_title("Pending Tasks") + cards

    posts = session.query(Post).order_by(Post.created_at.desc()).limit(20).all()
    if posts:
        rows = "".join(
            f"<tr>"
            f"<td>{escape_html(str(p.id))}</td>"
            f"<td>{escape_html(p.platform)}</td>"
            f"<td>{escape_html(p.topic[:50])}</td>"
            f"<td>{escape_html(p.status)}</td>"
            f"<td>{escape_html(p.provider_used or '-')}</td>"
            f"<td>{escape_html(p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else '')}</td>"
            f"</tr>"
            for p in posts
        )
        activity_html = f"""
        {section_title("Recent Activity")}
        <div class="table-responsive">
          <table class="table table-hover align-middle bg-white rounded-4 overflow-hidden">
            <thead class="table-light">
              <tr>
                <th>ID</th>
                <th>Platform</th>
                <th>Topic</th>
                <th>Status</th>
                <th>Provider</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """
    else:
        activity_html = (
            section_title("Recent Activity")
            + '<p class="text-muted">No posts yet. Create your first post from Create Post or AI Workspace.</p>'
        )

    return f"""
    <div class="cp-dashboard-content">
      {page_header("Dashboard", "Overview of your content pipeline, chatbot activity, publishing connectors, and system health.")}
      {alert}
      {metrics}
      {section_title("Provider Status")}
      {providers}
      {section_title("System Health")}
      <p class="mb-3">Overall: {badge(overall.title(), overall_kind)}</p>
      <div class="row g-4">{health_rows}</div>
      {section_title("Connector Health")}
      <div class="row g-4">{connector_cards}</div>
      {pending_html}
      {activity_html}
    </div>
  """


def render(session: Session) -> None:
    """Backward-compatible alias — layout calls render_html directly."""
    pass

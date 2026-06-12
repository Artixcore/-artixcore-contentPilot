"""Self-contained UI component helpers for Streamlit pages."""

from __future__ import annotations

import html

import streamlit as st

from ui.theme import TEXT_SECONDARY


def esc(value: str | int | float | None) -> str:
    return html.escape(str(value or ""))


def page_header(title: str, subtitle: str = "") -> None:
    sub = f'<p class="cp-page-subtitle">{esc(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f"""
    <div>
      <h1 class="cp-page-title">{esc(title)}</h1>
      {sub}
    </div>
    """,
        unsafe_allow_html=True,
    )


def section_title(title: str) -> None:
    st.markdown(f'<div class="cp-section-title">{esc(title)}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str | int, icon: str = "📊") -> None:
    st.markdown(
        f"""
    <div class="cp-metric-card">
      <div class="cp-metric-icon">{esc(icon)}</div>
      <div class="cp-metric-label">{esc(label)}</div>
      <div class="cp-metric-value">{esc(value)}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def status_badge(text: str, status: str = "success") -> str:
    variant = {
        "success": "cp-badge-success",
        "configured": "cp-badge-success",
        "healthy": "cp-badge-success",
        "approved": "cp-badge-success",
        "published": "cp-badge-success",
        "warning": "cp-badge-warning",
        "pending": "cp-badge-warning",
        "missing": "cp-badge-warning",
        "danger": "cp-badge-danger",
        "error": "cp-badge-danger",
        "rejected": "cp-badge-danger",
        "info": "cp-badge-info",
        "muted": "cp-badge-warning",
    }.get(status.lower(), "cp-badge-warning")
    return f'<span class="cp-badge {variant}">{esc(text)}</span>'


def badge_html(text: str, status: str = "success") -> str:
    return status_badge(text, status)


def status_card(title: str, message: str, status: str = "success") -> None:
    badge = status_badge(status.title(), status)
    st.markdown(
        f"""
    <div class="cp-status-card">
      <div class="d-flex justify-content-between align-items-start gap-3">
        <div>
          <div class="cp-status-title">{esc(title)}</div>
          <div class="cp-status-text">{esc(message)}</div>
        </div>
        {badge}
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def info_card(title: str, body: str) -> None:
    st.markdown(
        f"""
    <div class="cp-card">
      <h5>{esc(title)}</h5>
      <p class="mb-0 text-muted">{esc(body)}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def alert_card(message: str, kind: str = "info") -> None:
    kind_map = {"error": "error", "warning": "warning", "info": "info", "success": "success"}
    cls = f"cp-alert cp-alert-{kind_map.get(kind, 'info')}"
    st.markdown(
        f'<div class="{cls}" role="alert">{esc(message)}</div>',
        unsafe_allow_html=True,
    )


def render_alert(message: str, kind: str = "info") -> None:
    if kind == "error":
        st.error(message)
    elif kind == "warning":
        st.warning(message)
    elif kind == "success":
        st.success(message)
    else:
        st.info(message)


def welcome_card() -> None:
    st.markdown(
        """
    <div class="cp-welcome-card">
      <div class="cp-logo-mark">A</div>
      <h2 style="font-weight:800;margin-bottom:10px;">Welcome to Artixcore ContentPilot</h2>
      <p class="text-muted mb-1">Your AI content, chatbot, and publishing command center.</p>
      <p class="text-muted mb-0">Generate, approve, publish, and learn from every conversation.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def template_card(title: str, description: str = "") -> None:
    st.markdown(
        f"""
    <div class="cp-template-card">
      <div class="d-flex gap-3">
        <span style="font-size:1.4rem;">⚡</span>
        <div>
          <div class="fw-semibold">{esc(title)}</div>
          <p class="text-muted mb-0" style="font-size:0.9rem;">{esc(description)}</p>
        </div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def platform_badge(platform: str) -> str:
    colors = {
        "linkedin": "#0A66C2",
        "facebook": "#1877F2",
        "instagram": "#E4405F",
        "twitter": "#000000",
        "website_blog": "#D97706",
        "telegram": "#0088CC",
    }
    color = colors.get(platform.lower(), "#6B7280")
    plat_label = platform.replace("_", " ").title()
    return (
        f'<span class="cp-platform-badge" style="background:{color}15;color:{color};'
        f'border:1px solid {color}30;">{esc(plat_label)}</span>'
    )


def queue_card(title: str, badges_html: str, preview: str, meta: str) -> None:
    preview_text = esc(preview[:200]) + ("..." if len(preview) > 200 else "")
    st.markdown(
        f"""
    <div class="cp-card" style="margin-bottom:12px;">
      <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
        <span class="fw-semibold">{esc(title)}</span>
        <span>{badges_html}</span>
      </div>
      <p class="text-muted mb-2" style="font-size:0.9rem;">{preview_text}</p>
      <div style="font-size:0.82rem;color:{TEXT_SECONDARY};">{esc(meta)}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def chat_message(role: str, content: str, provider: str = "") -> None:
    body = esc(content).replace("\n", "<br>")
    if role == "user":
        st.markdown(
            f'<div class="cp-message user"><div class="cp-message-body">{body}</div></div>',
            unsafe_allow_html=True,
        )
        return
    meta = f'<div style="font-size:0.75rem;color:#9ca3af;margin-top:8px;">Model: {esc(provider)}</div>' if provider else ""
    st.markdown(
        f"""
    <div class="cp-message ai">
      <div class="cp-logo-mark cp-message-avatar">A</div>
      <div class="cp-message-body">{body}{meta}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def date_divider(label: str = "TODAY") -> None:
    st.markdown(f'<div class="cp-date-divider">{esc(label)}</div>', unsafe_allow_html=True)


def inbox_item(name: str, preview: str, status: str, platform: str, active: bool = False) -> None:
    item_cls = "cp-inbox-item active" if active else "cp-inbox-item"
    st.markdown(
        f"""
    <div class="{item_cls}">
      <div class="d-flex justify-content-between align-items-start gap-2 mb-1">
        <strong>{esc(name)}</strong>
        {status_badge(status, "info")}
      </div>
      <div class="text-muted" style="font-size:0.82rem;margin-bottom:6px;">{esc(preview[:60])}</div>
      {platform_badge(platform)}
    </div>
    """,
        unsafe_allow_html=True,
    )


def connector_row(name: str, configured: bool, detail: str = "") -> None:
    desc = f'<p class="cp-status-text mb-0 mt-2">{esc(detail)}</p>' if detail else ""
    st.markdown(
        f"""
    <div class="cp-status-card" style="margin-bottom:10px;min-height:auto;">
      <div class="d-flex justify-content-between align-items-start gap-2">
        <span class="cp-status-title">{esc(name)}</span>
        {status_badge("Configured" if configured else "Missing", "success" if configured else "warning")}
      </div>
      {desc}
    </div>
    """,
        unsafe_allow_html=True,
    )


# Backward-compatible aliases
render_page_header = page_header
render_section_title = section_title
render_metric_card = metric_card
render_status_badge = status_badge
render_provider_card = lambda name, configured, description="": status_card(
    name, description or ("Configured." if configured else "Not configured."), "success" if configured else "warning"
)
render_health_card = status_card
render_info_card = info_card
render_alert_card = alert_card
render_welcome_hero = welcome_card
render_template_card = template_card
render_chat_message = chat_message
render_date_divider = date_divider
render_queue_card = queue_card

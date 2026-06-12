"""Bootstrap 5 HTML component builders — all functions return complete HTML strings."""

from __future__ import annotations

import html

PRIMARY_NAV = [
    ("Dashboard", "bi-grid", "dashboard"),
    ("AI Workspace", "bi-stars", "ai_workspace"),
    ("Create Post", "bi-pencil-square", "create_post"),
    ("Approvals", "bi-check2-square", "approvals"),
    ("Chat Inbox", "bi-chat-dots", "chat_inbox"),
    ("Chat Control", "bi-robot", "chat_control"),
    ("Publish Center", "bi-send", "publish_center"),
]

SYSTEM_NAV = [
    ("Training Data", "bi-bullseye", "training_data"),
    ("Provider Settings", "bi-cpu", "provider_settings"),
    ("Publishing Settings", "bi-share", "publishing_settings"),
    ("Brand Settings", "bi-palette", "brand_settings"),
    ("Exports", "bi-download", "exports"),
]

ICON_RAIL = [
    ("bi-grid", "dashboard"),
    ("bi-stars", "ai_workspace"),
    ("bi-pencil-square", "create_post"),
    ("bi-chat-dots", "chat_inbox"),
    ("bi-send", "publish_center"),
    ("bi-bullseye", "training_data"),
    ("bi-gear", "provider_settings"),
]

WORKSPACES = ["Artixcore", "Dealzyro", "Digitalplanup", "General"]


def escape_html(text: str | None) -> str:
    return html.escape(str(text or ""))


html_escape = escape_html


def badge(text: str, variant: str = "secondary") -> str:
    variant_map = {
        "success": "success",
        "configured": "success",
        "healthy": "success",
        "approved": "success",
        "published": "success",
        "warning": "warning",
        "pending": "warning",
        "missing": "warning",
        "danger": "danger",
        "error": "danger",
        "rejected": "danger",
        "info": "info",
        "muted": "secondary",
    }
    bs = variant_map.get(variant.lower(), "secondary")
    return f'<span class="badge text-bg-{bs} cp-badge">{html_escape(text)}</span>'


def metric_card(title: str, value: str | int, icon: str = "bi-bar-chart") -> str:
    return f"""
    <div class="col-12 col-sm-6 col-xl">
      <div class="card cp-metric-card border rounded-4 shadow-sm h-100">
        <div class="card-body">
          <div class="cp-metric-icon"><i class="bi {html_escape(icon)}"></i></div>
          <div class="cp-metric-label">{html_escape(title)}</div>
          <div class="cp-metric-value">{html_escape(str(value))}</div>
        </div>
      </div>
    </div>
    """


def status_card(title: str, description: str, status: str, configured: bool | None = None) -> str:
    if configured is not None:
        label = "Configured" if configured else "Not Configured"
        kind = "success" if configured else "warning"
    else:
        label = status.title()
        kind = {"healthy": "success", "warning": "warning", "error": "danger"}.get(status.lower(), "muted")
    desc = f'<p class="cp-card-subtitle mb-0">{html_escape(description)}</p>' if description else ""
    return f"""
    <div class="col-12 col-md-6 col-lg-4">
      <div class="card cp-status-card border rounded-4 shadow-sm h-100">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
            <span class="fw-semibold">{html_escape(title)}</span>
            {badge(label, kind)}
          </div>
          {desc}
        </div>
      </div>
    </div>
    """


def provider_card(name: str, configured: bool, description: str = "") -> str:
    return status_card(name, description, "", configured=configured)


def health_card(name: str, status: str, message: str) -> str:
    return status_card(name, message, status)


def nav_link(label: str, icon: str, view: str, active_view: str, workspace: str = "Artixcore") -> str:
    active = " active" if view == active_view else ""
    href = f"?view={html_escape(view)}&workspace={html_escape(workspace)}"
    return (
        f'<a href="{href}" class="cp-nav-link{active}">'
        f'<i class="bi {html_escape(icon)}"></i><span>{html_escape(label)}</span></a>'
    )


def icon_link(icon: str, view: str, active_view: str, workspace: str = "Artixcore", title: str = "") -> str:
    active = " active" if view == active_view else ""
    href = f"?view={html_escape(view)}&workspace={html_escape(workspace)}"
    t = f' title="{html_escape(title)}"' if title else ""
    return f'<a href="{href}" class="cp-icon-link{active}"{t}><i class="bi {html_escape(icon)}"></i></a>'


def premium_card() -> str:
    return """
    <div class="cp-premium-card mt-4">
      <div class="cp-upgrade-title">Premium Plan</div>
      <div class="cp-upgrade-text">Unlock advanced automation, team approval, analytics, and cloud publishing.</div>
      <a href="#" class="btn btn-light btn-sm cp-premium-btn mt-3">Upgrade Premium</a>
    </div>
    """


def page_header(title: str, subtitle: str | None = None) -> str:
    sub = f'<p class="cp-page-subtitle">{html_escape(subtitle)}</p>' if subtitle else ""
    return f'<h1 class="cp-page-title">{html_escape(title)}</h1>{sub}'


def section_title(title: str) -> str:
    return f'<div class="cp-section-label">{html_escape(title)}</div>'


def topbar(current_title: str) -> str:
    return f"""
    <header class="cp-topbar">
      <div class="d-flex align-items-center gap-2">
        <button type="button" class="btn btn-outline-secondary btn-sm cp-mobile-menu" data-cp-mobile-menu aria-label="Open menu">
          <i class="bi bi-list"></i>
        </button>
        <span class="cp-topbar-title">{escape_html(current_title)}</span>
      </div>
      <div class="cp-topbar-actions">
        <a href="#" class="btn btn-outline-secondary btn-sm cp-topbar-btn">Upgrade Plan</a>
        <a href="#" class="btn btn-outline-secondary btn-sm cp-topbar-btn">History</a>
        <a href="?view=chat_inbox" class="cp-topbar-icon" title="Inbox"><i class="bi bi-inbox"></i></a>
        <a href="#" class="cp-topbar-icon" title="Share"><i class="bi bi-share"></i></a>
        <a href="#" class="cp-topbar-icon" title="Notifications"><i class="bi bi-bell"></i></a>
        <a href="?view=brand_settings" class="cp-topbar-icon" title="Profile"><i class="bi bi-person-circle"></i></a>
      </div>
    </header>
    """


def sidebar(active_view: str, workspace: str = "Artixcore") -> str:
    primary = "".join(nav_link(l, i, v, active_view, workspace) for l, i, v in PRIMARY_NAV)
    system = "".join(nav_link(l, i, v, active_view, workspace) for l, i, v in SYSTEM_NAV)
    projects = "".join(
        f'<a href="?view={html_escape(active_view)}&workspace={html_escape(ws)}" '
        f'class="cp-nav-link cp-project-link{" active" if ws == workspace else ""}">'
        f'<i class="bi bi-folder2"></i><span>{html_escape(ws)}</span></a>'
        for ws in WORKSPACES
    )
    return f"""
    <aside class="cp-sidebar" id="cp-sidebar">
      <div class="cp-sidebar-brand">
        <div class="cp-sidebar-title">Artixcore Pilot</div>
        <div class="cp-sidebar-subtitle">ContentPilot</div>
      </div>
      <div class="cp-sidebar-actions d-grid gap-2 mb-3">
        <a href="?view=create_post&workspace={html_escape(workspace)}" class="btn cp-primary-btn btn-sm">+ New Content</a>
        <a href="?view=ai_workspace&workspace={html_escape(workspace)}" class="btn cp-secondary-btn btn-sm">Import</a>
      </div>
      <div class="cp-search-wrap mb-3">
        <i class="bi bi-search"></i>
        <input type="search" class="form-control form-control-sm cp-search" placeholder="Search..." aria-label="Search">
      </div>
      <div class="cp-nav-group-label">Primary</div>
      <nav class="cp-nav-group mb-3">{primary}</nav>
      <div class="cp-nav-group-label">System</div>
      <nav class="cp-nav-group mb-3">{system}</nav>
      <div class="cp-nav-group-label">Works / Projects</div>
      <nav class="cp-nav-group mb-2">{projects}</nav>
      {premium_card()}
    </aside>
    """


def icon_rail(active_view: str, workspace: str = "Artixcore") -> str:
    icons = "".join(icon_link(i, v, active_view, workspace) for i, v in ICON_RAIL)
    return f"""
    <aside class="cp-icon-rail">
      <a href="?view=dashboard&workspace={html_escape(workspace)}" class="cp-logo" title="Artixcore">A</a>
      <nav class="cp-icon-rail-nav">{icons}</nav>
      <div class="cp-icon-rail-bottom">
        <a href="#" class="cp-icon-link" title="Theme"><i class="bi bi-sun"></i></a>
        <a href="?view=provider_settings&workspace={html_escape(workspace)}" class="cp-icon-link" title="Settings"><i class="bi bi-sliders"></i></a>
        <div class="cp-avatar" title="Profile">S</div>
      </div>
    </aside>
    """


def error_card(title: str, message: str, reason: str | None = None, action: str | None = None) -> str:
    reason_html = f'<p class="mb-2"><strong>Reason:</strong> {escape_html(reason)}</p>' if reason else ""
    action_html = f'<p class="mb-0 text-muted"><em>{escape_html(action)}</em></p>' if action else ""
    return f"""
    <div class="card cp-card border rounded-4 shadow-sm">
      <div class="card-body">
        <h2 class="h5 fw-bold text-danger mb-3">{escape_html(title)}</h2>
        <p class="mb-2">{escape_html(message)}</p>
        {reason_html}
        {action_html}
      </div>
    </div>
    """


def alert_html(message: str, kind: str = "info") -> str:
    kind_map = {"error": "danger", "warning": "warning", "info": "info", "success": "success"}
    bs = kind_map.get(kind, "info")
    return f'<div class="alert alert-{bs} cp-alert" role="alert">{html_escape(message)}</div>'


def queue_card(title: str, badges_html: str, preview: str, meta: str) -> str:
    preview_text = html_escape(preview[:200]) + ("..." if len(preview) > 200 else "")
    return f"""
    <div class="card cp-card border rounded-4 shadow-sm mb-3">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
          <span class="fw-semibold">{html_escape(title)}</span>
          <span>{badges_html}</span>
        </div>
        <p class="cp-card-subtitle mb-2">{preview_text}</p>
        <div class="cp-card-meta">{html_escape(meta)}</div>
      </div>
    </div>
    """


def template_card(title: str, description: str = "") -> str:
    return f"""
    <div class="col-12 col-md-6">
      <div class="card cp-template-card border rounded-4 shadow-sm h-100">
        <div class="card-body d-flex gap-3">
          <i class="bi bi-lightning-charge fs-4 text-warning"></i>
          <div>
            <div class="fw-semibold">{html_escape(title)}</div>
            <p class="cp-card-subtitle mb-0">{html_escape(description)}</p>
          </div>
        </div>
      </div>
    </div>
    """


def welcome_hero() -> str:
    return """
    <div class="cp-welcome-hero text-center py-4">
      <div class="cp-logo-mark mx-auto">A</div>
      <h2 class="cp-welcome-title">Welcome to Artixcore ContentPilot</h2>
      <p class="cp-welcome-sub">Your AI content, chatbot, and publishing command center.</p>
      <p class="cp-welcome-sub2">Generate, approve, publish, and learn from every conversation.</p>
    </div>
    """


def chat_message_html(role: str, content: str, provider: str = "", show_actions: bool = False) -> str:
    body = html_escape(content).replace("\n", "<br>")
    if role == "user":
        return f'<div class="cp-message user"><div class="cp-message-body">{body}</div></div>'
    meta = ""
    if show_actions or provider:
        actions = "Copy · Like · Dislike · Regenerate" if show_actions else ""
        provider_label = f"Model: {html_escape(provider)}" if provider else ""
        meta = f'<div class="cp-chat-meta">{provider_label} {actions}</div>'
    return f"""
    <div class="cp-message ai">
      <div class="cp-logo-mark cp-message-avatar">A</div>
      <div class="cp-message-body">{body}{meta}</div>
    </div>
    """


def date_divider(label: str = "TODAY") -> str:
    return f'<div class="cp-date-divider">{html_escape(label)}</div>'


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
        f'<span class="badge cp-platform-badge" style="background:{color}15;color:{color};'
        f'border:1px solid {color}30;">{html_escape(plat_label)}</span>'
    )


def app_shell(active_view: str, page_html: str, page_title: str, workspace: str = "Artixcore") -> str:
    """Return a complete self-contained app shell with page content."""
    return f"""
    <div class="cp-bg">
      <div class="cp-shell">
        {icon_rail(active_view, workspace)}
        {sidebar(active_view, workspace)}
        <main class="cp-main">
          {topbar(page_title)}
          <section class="cp-page">
            {page_html}
          </section>
        </main>
      </div>
    </div>
    """


def chrome_only(active_view: str, page_title: str, workspace: str = "Artixcore") -> str:
    """Shell with empty page area — interactive Streamlit widgets render below."""
    return app_shell(active_view, "", page_title, workspace)


def widget_section_header(title: str, subtitle: str | None = None) -> str:
    """Self-contained header block for the Streamlit widget area below chrome."""
    sub = f'<p class="cp-page-subtitle mb-0">{html_escape(subtitle)}</p>' if subtitle else ""
    return f"""
    <div class="cp-widget-header">
      <h1 class="cp-page-title">{html_escape(title)}</h1>
      {sub}
    </div>
    """

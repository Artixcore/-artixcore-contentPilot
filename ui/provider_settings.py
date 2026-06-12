"""Provider settings page."""

import os

import streamlit as st
from sqlalchemy.orm import Session

from core.models import ProviderLog
from core.router import ProviderRouter
from core.utils import mask_secret
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.components import (
    render_alert,
    render_connector_status,
    render_data_table_or_cards,
    render_page_header,
    render_section_header,
)


def render(session: Session) -> None:
    render_page_header("Provider Settings", "AI provider status and configuration.")

    router = ProviderRouter(session=session)
    availability = router.get_availability_status()

    if not availability.get("openai") and not availability.get("anthropic"):
        render_alert(PROVIDER_UNAVAILABLE_MSG, "error")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            render_connector_status("OpenAI", bool(availability.get("openai")))
            st.caption(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}")
            st.caption(f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}")
    with c2:
        with st.container(border=True):
            render_connector_status("Anthropic", bool(availability.get("anthropic")))
            st.caption(f"Model: {os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-latest')}")
            st.caption(f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}")

    with st.container(border=True):
        render_section_header("Configuration")
        st.markdown(
        """
Configure API keys in your `.env` file (copy from `.env.example`):

```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini

ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

**Never commit your `.env` file.** Restart the app after updating environment variables.
        """
        )

    render_section_header("Provider Router Modes")
    st.markdown(
        """
| Mode | Behavior |
|------|----------|
| **auto** | OpenAI → Anthropic |
| **quality** | Anthropic → OpenAI |
| **manual** | Selected provider only (must be available) |
| **fallback** | Selected → other available provider |
        """
    )

    render_section_header("Recent Provider Logs")
    logs = session.query(ProviderLog).order_by(ProviderLog.created_at.desc()).limit(15).all()
    if logs:
        rows = [
            {
                "provider": log.provider,
                "model": log.model or "-",
                "task": log.task_type,
                "success": "Yes" if log.success else "No",
                "latency": log.latency_ms or "-",
                "error": (log.error_message or "-")[:50],
                "time": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "",
            }
            for log in logs
        ]
        render_data_table_or_cards(
            rows,
            [
                ("provider", "Provider"),
                ("model", "Model"),
                ("task", "Task"),
                ("success", "Success"),
                ("latency", "Latency (ms)"),
                ("error", "Error"),
                ("time", "Time"),
            ],
        )
    else:
        st.info("No provider logs yet. Generate a post to see activity.")

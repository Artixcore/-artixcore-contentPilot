"""Provider settings page."""

import os

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from core.models import ProviderLog
from core.router import ProviderRouter
from core.utils import mask_secret
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.components import alert_card, page_header, section_title, status_card


def render_provider_settings(session: Session) -> None:
    page_header("Provider Settings", "AI provider status and configuration.")

    router = ProviderRouter(session=session)
    availability = router.get_availability_status()

    if not availability.get("openai") and not availability.get("anthropic"):
        alert_card(PROVIDER_UNAVAILABLE_MSG, "error")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            status_card(
                "OpenAI",
                "Configured." if availability.get("openai") else "API key missing.",
                "success" if availability.get("openai") else "warning",
            )
            st.caption(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}")
            st.caption(f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}")
    with c2:
        with st.container(border=True):
            status_card(
                "Anthropic",
                "Configured." if availability.get("anthropic") else "API key missing.",
                "success" if availability.get("anthropic") else "warning",
            )
            st.caption(f"Model: {os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-latest')}")
            st.caption(f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}")

    with st.container(border=True):
        section_title("Configuration")
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

    section_title("Provider Router Modes")
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

    section_title("Recent Provider Logs")
    logs = session.query(ProviderLog).order_by(ProviderLog.created_at.desc()).limit(15).all()
    if logs:
        df = pd.DataFrame(
            [
                {
                    "Provider": log.provider,
                    "Model": log.model or "-",
                    "Task": log.task_type,
                    "Success": "Yes" if log.success else "No",
                    "Latency (ms)": log.latency_ms or "-",
                    "Error": (log.error_message or "-")[:50],
                    "Time": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "",
                }
                for log in logs
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No provider logs yet. Generate a post to see activity.")


def render(session: Session) -> None:
    render_provider_settings(session)

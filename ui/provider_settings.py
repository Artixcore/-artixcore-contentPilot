"""Provider settings page."""

import os

import streamlit as st
from sqlalchemy.orm import Session

from core.models import ProviderLog
from core.router import ProviderRouter
from core.utils import mask_secret
from providers import PROVIDER_UNAVAILABLE_MSG
from ui.bootstrap_components import alert_html, badge, section_title, widget_section_header


def render(session: Session) -> None:
    st.markdown(
        widget_section_header("Provider Settings", "AI provider status and configuration."),
        unsafe_allow_html=True,
    )

    router = ProviderRouter(session=session)
    availability = router.get_availability_status()

    if not availability.get("openai") and not availability.get("anthropic"):
        st.markdown(alert_html(PROVIDER_UNAVAILABLE_MSG, "error"), unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown(
                f'<div class="d-flex justify-content-between mb-2"><span class="fw-semibold">OpenAI</span>'
                f'{badge("Configured" if availability.get("openai") else "Missing", "success" if availability.get("openai") else "warning")}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}")
            st.caption(f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}")
    with c2:
        with st.container(border=True):
            st.markdown(
                f'<div class="d-flex justify-content-between mb-2"><span class="fw-semibold">Anthropic</span>'
                f'{badge("Configured" if availability.get("anthropic") else "Missing", "success" if availability.get("anthropic") else "warning")}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"Model: {os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-latest')}")
            st.caption(f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}")

    with st.container(border=True):
        st.markdown(section_title("Configuration"), unsafe_allow_html=True)
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

    st.markdown(section_title("Provider Router Modes"), unsafe_allow_html=True)
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

    st.markdown(section_title("Recent Provider Logs"), unsafe_allow_html=True)
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
        import pandas as pd

        df = pd.DataFrame([{
            "Provider": r["provider"],
            "Model": r["model"],
            "Task": r["task"],
            "Success": r["success"],
            "Latency (ms)": r["latency"],
            "Error": r["error"],
            "Time": r["time"],
        } for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No provider logs yet. Generate a post to see activity.")

"""Provider settings page."""

import os

import streamlit as st
from sqlalchemy.orm import Session

from core.models import ProviderLog
from core.router import ProviderRouter
from core.utils import mask_secret
from providers import PROVIDER_UNAVAILABLE_MSG


def render(session: Session) -> None:
    st.title("Provider Settings")
    st.caption("AI provider status and configuration.")

    router = ProviderRouter(session=session)
    availability = router.get_availability_status()

    if not availability.get("openai") and not availability.get("anthropic"):
        st.error(PROVIDER_UNAVAILABLE_MSG)

    st.subheader("Provider Status")
    c1, c2 = st.columns(2)

    with c1:
        if availability.get("openai"):
            st.success("OpenAI: Available")
        else:
            st.warning("OpenAI: Missing API Key")
        st.caption(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}")
        st.caption(f"Key: {mask_secret(os.getenv('OPENAI_API_KEY', ''))}")

    with c2:
        if availability.get("anthropic"):
            st.success("Anthropic: Available")
        else:
            st.warning("Anthropic: Missing API Key")
        st.caption(f"Model: {os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-latest')}")
        st.caption(f"Key: {mask_secret(os.getenv('ANTHROPIC_API_KEY', ''))}")

    st.divider()
    st.subheader("Configuration")
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

    st.divider()
    st.subheader("Provider Router Modes")
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

    st.divider()
    st.subheader("Recent Provider Logs")
    logs = session.query(ProviderLog).order_by(ProviderLog.created_at.desc()).limit(15).all()
    if logs:
        rows = [
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
        import pandas as pd

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No provider logs yet. Generate a post to see activity.")

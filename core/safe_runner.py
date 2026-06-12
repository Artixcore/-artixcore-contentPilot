"""Safe execution wrappers for sync, async, and Streamlit actions."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from core.error_handler import handle_exception, log_exception
from core.logging_config import get_logger
from core.rate_limiter import check_rate_limit

logger = get_logger(__name__)

T = TypeVar("T")

_RATE_LIMIT_ACTIONS = {
    "generate_post": "ai_generation",
    "generate_chatbot_reply": "chatbot_reply",
    "approve_post": "ai_generation",
    "reject_post": "ai_generation",
    "publish_post": "publishing",
    "export_data": "export",
    "save_settings": "ai_generation",
    "upload_media": "ai_generation",
    "telegram_command": "telegram_command",
    "social_connector": "publishing",
    "training_data_export": "export",
}


def safe_execute(
    fn: Callable[..., T],
    *args,
    fallback: T | None = None,
    context: str | None = None,
    raise_on_error: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """Execute fn safely, returning structured result."""
    try:
        result = fn(*args, **kwargs)
        return {"success": True, "result": result, "error": None}
    except Exception as exc:
        error = handle_exception(exc, context=context)
        if raise_on_error:
            raise
        return {"success": False, "result": fallback, "error": error}


async def safe_async_execute(
    fn: Callable[..., Any],
    *args,
    fallback: Any = None,
    context: str | None = None,
    raise_on_error: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """Execute async callable safely."""
    try:
        if asyncio.iscoroutinefunction(fn):
            result = await fn(*args, **kwargs)
        else:
            result = fn(*args, **kwargs)
        return {"success": True, "result": result, "error": None}
    except Exception as exc:
        error = handle_exception(exc, context=context)
        if raise_on_error:
            raise
        return {"success": False, "result": fallback, "error": error}


def safe_streamlit_action(
    action_name: str,
    fn: Callable[..., T],
    *args,
    rate_limit: bool = True,
    load_type: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Wrap a Streamlit button action with rate limiting and error handling."""
    try:
        if rate_limit:
            rl_action = _RATE_LIMIT_ACTIONS.get(action_name, action_name)
            check_rate_limit(rl_action)
        if load_type:
            from core.load_manager import with_load_slot

            with with_load_slot(load_type):
                return safe_execute(fn, *args, context=action_name, **kwargs)
        return safe_execute(fn, *args, context=action_name, **kwargs)
    except Exception as exc:
        log_exception(exc, context=action_name)
        return {"success": False, "result": None, "error": handle_exception(exc, context=action_name)}

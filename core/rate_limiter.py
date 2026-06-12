"""Local in-memory rate limiter."""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from core.errors import RateLimitError
from core.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_LIMITS: dict[str, int] = {
    "ai_generation": int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "20")),
    "chatbot_reply": int(os.getenv("CHAT_RATE_LIMIT_PER_MINUTE", "30")),
    "publishing": int(os.getenv("PUBLISH_RATE_LIMIT_PER_MINUTE", "10")),
    "export": int(os.getenv("EXPORT_RATE_LIMIT_PER_MINUTE", "5")),
    "telegram_command": int(os.getenv("TELEGRAM_RATE_LIMIT_PER_MINUTE", "30")),
}

_WINDOWS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = threading.Lock()
_WINDOW_SECONDS = 60.0


def _get_limit(action: str) -> int:
    return _DEFAULT_LIMITS.get(action, 30)


def check_rate_limit(action: str, key: str = "default") -> int:
    """
    Check rate limit for action/key. Returns remaining requests.
    Raises RateLimitError if limit exceeded.
    """
    composite_key = f"{action}:{key}"
    limit = _get_limit(action)
    now = time.monotonic()
    cutoff = now - _WINDOW_SECONDS

    with _LOCK:
        window = _WINDOWS[composite_key]
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= limit:
            logger.warning("Rate limit triggered: action=%s key=%s", action, key)
            raise RateLimitError()
        window.append(now)
        return limit - len(window)


def reset_rate_limits() -> None:
    """Reset all rate limit windows (for tests)."""
    with _LOCK:
        _WINDOWS.clear()


def get_rate_limit_status(action: str, key: str = "default") -> dict:
    composite_key = f"{action}:{key}"
    limit = _get_limit(action)
    now = time.monotonic()
    cutoff = now - _WINDOW_SECONDS
    with _LOCK:
        window = _WINDOWS[composite_key]
        while window and window[0] < cutoff:
            window.popleft()
        used = len(window)
    return {"action": action, "limit": limit, "used": used, "remaining": max(0, limit - used)}

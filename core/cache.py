"""Lightweight TTL cache for repeated reads."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

_TTL_DEFAULTS: dict[str, int] = {
    "provider_status": int(os.getenv("CACHE_PROVIDER_STATUS_TTL", "60")),
    "connector_status": int(os.getenv("CACHE_CONNECTOR_STATUS_TTL", "60")),
    "dashboard_stats": int(os.getenv("CACHE_DASHBOARD_STATS_TTL", "30")),
    "settings": int(os.getenv("CACHE_SETTINGS_TTL", "30")),
    "brand_profile": int(os.getenv("CACHE_SETTINGS_TTL", "30")),
}

_STORE: dict[str, tuple[float, Any]] = {}
_LOCK = threading.Lock()


def _ttl_for(key: str, ttl: int | None) -> int:
    if ttl is not None:
        return ttl
    for prefix, default_ttl in _TTL_DEFAULTS.items():
        if key.startswith(prefix):
            return default_ttl
    return 30


def get(key: str) -> Any | None:
    with _LOCK:
        entry = _STORE.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del _STORE[key]
            return None
        return value


def set(key: str, value: Any, ttl: int | None = None) -> None:
    ttl_seconds = _ttl_for(key, ttl)
    with _LOCK:
        _STORE[key] = (time.monotonic() + ttl_seconds, value)


def get_or_set(key: str, fn: Callable[[], T], ttl: int | None = None) -> T:
    cached = get(key)
    if cached is not None:
        return cached
    value = fn()
    set(key, value, ttl=ttl)
    return value


def invalidate(*keys: str) -> None:
    with _LOCK:
        for key in keys:
            _STORE.pop(key, None)


def invalidate_prefix(prefix: str) -> None:
    with _LOCK:
        to_delete = [k for k in _STORE if k.startswith(prefix)]
        for key in to_delete:
            del _STORE[key]


def clear_cache() -> None:
    with _LOCK:
        _STORE.clear()

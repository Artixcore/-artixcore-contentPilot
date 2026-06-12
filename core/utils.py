"""Shared utilities for ContentPilot."""

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() in ("true", "1", "yes")
APP_ENV = os.getenv("APP_ENV", "development")

PLATFORM_RULES = {
    "facebook": (
        "Facebook rules: Friendly business tone, medium length, CTA allowed, "
        "3 to 6 hashtags."
    ),
    "instagram": (
        "Instagram rules: Shorter caption, visual and emotional tone, "
        "8 to 15 hashtags, include image idea or image prompt."
    ),
    "linkedin": (
        "LinkedIn rules: Professional and B2B, strong hook, insight-driven, "
        "minimal hashtags (3 to 5 max)."
    ),
    "twitter": (
        "Twitter/X rules: Short post under 280 characters by default, "
        "optionally allow thread-style output, sharp, direct, and memorable."
    ),
    "website_blog": (
        "Website Blog rules: Include SEO title, meta description, slug, "
        "blog outline, full article draft, and CTA section."
    ),
}


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        logger.warning("Prompt file not found: %s", name)
        return ""
    return path.read_text(encoding="utf-8")


def parse_json_response(raw: str) -> dict | None:
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
    return None


def get_platform_rules(platform: str) -> str:
    return PLATFORM_RULES.get(platform, "Follow general social media best practices.")


def mask_secret(value: str) -> str:
    if not value:
        return "Not configured"
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def hashtags_to_json(hashtags: list[str]) -> str:
    return json.dumps(hashtags or [])


def hashtags_from_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(h) for h in data]
    except json.JSONDecodeError:
        pass
    return []


def platforms_to_json(platforms: list[str]) -> str:
    return json.dumps(platforms or [])


def platforms_from_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(p) for p in data]
    except json.JSONDecodeError:
        pass
    return []


def format_user_error(message: str, exc: Exception | None = None) -> str:
    if APP_DEBUG and exc:
        return f"{message}\n\nDebug: {type(exc).__name__}: {exc}"
    return message


SENSITIVE_KEYS = frozenset({
    "authorization",
    "access_token",
    "refresh_token",
    "api_key",
    "api_secret",
    "client_secret",
    "token",
    "password",
    "secret",
})


def sanitize_payload(data: object) -> str:
    """Strip sensitive fields before logging."""

    def _redact(obj: object) -> object:
        if isinstance(obj, dict):
            return {
                k: "****" if str(k).lower() in SENSITIVE_KEYS or "token" in str(k).lower() else _redact(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_redact(item) for item in obj]
        return obj

    try:
        return json.dumps(_redact(data), ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return "{}"


def has_any_ai_provider() -> bool:
    from providers import get_all_providers

    return any(p.is_available() for p in get_all_providers().values())


def log_content_event(
    session,
    post_id: int,
    event_type: str,
    event_data: dict | None = None,
) -> None:
    from core.models import ContentEvent

    event = ContentEvent(
        post_id=post_id,
        event_type=event_type,
        event_data=json.dumps(event_data or {}, ensure_ascii=False),
    )
    session.add(event)
    session.flush()

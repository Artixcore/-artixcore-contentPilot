"""X / Twitter publisher via API v2."""

import logging
import os

import httpx

from publishers.base import BasePublisher

logger = logging.getLogger(__name__)

TIMEOUT = 30.0
MAX_LENGTH = 280


class XPublisher(BasePublisher):
    name = "twitter"
    circuit_name = "twitter"

    def __init__(self):
        self.access_token = os.getenv("X_ACCESS_TOKEN", "").strip()

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def publish_text(self, content: str, **kwargs) -> dict:
        if not content or not content.strip():
            return self._result(False, self.name, error="Content cannot be empty.")
        if not self.access_token:
            return self._result(False, self.name, error="X access token is not configured.")
        text = content.strip()
        if len(text) > MAX_LENGTH:
            return self._result(
                False,
                self.name,
                error=f"X posts must be {MAX_LENGTH} characters or fewer (got {len(text)}).",
            )

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"text": text}
        try:
            response = self._safe_request(
                "POST",
                "https://api.x.com/2/tweets",
                timeout=TIMEOUT,
                json=payload,
                headers=headers,
            )
            raw = self._parse_json_response(response)

            if response.status_code >= 400:
                error_msg = ""
                if isinstance(raw, dict):
                    errors = raw.get("errors", [])
                    if errors:
                        error_msg = errors[0].get("detail", errors[0].get("message", ""))
                    if not error_msg:
                        error_msg = raw.get("detail", raw.get("title", response.text[:200]))
                else:
                    error_msg = response.text[:200]
                return self._result(
                    False,
                    self.name,
                    error=f"X API error ({response.status_code}): {error_msg}",
                    raw_response=raw if isinstance(raw, dict) else {},
                )

            tweet_id = ""
            if isinstance(raw, dict):
                tweet_id = str(raw.get("data", {}).get("id", ""))
            post_url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else ""
            return self._result(
                True,
                self.name,
                external_post_id=tweet_id,
                external_post_url=post_url,
                raw_response=raw if isinstance(raw, dict) else {},
            )
        except httpx.TimeoutException:
            return self._result(False, self.name, error="X request timed out.")
        except Exception as exc:
            logger.warning("X publish failed: %s", type(exc).__name__)
            return self._result(False, self.name, error=f"X publish failed: {type(exc).__name__}")

    def publish_image(self, content: str, image_url: str, **kwargs) -> dict:
        return self.publish_text(content, **kwargs)

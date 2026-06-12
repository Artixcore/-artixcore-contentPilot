"""Meta Facebook Page publisher."""

import logging
import os

import httpx

from publishers.base import BasePublisher

logger = logging.getLogger(__name__)

TIMEOUT = 30.0


class MetaFacebookPublisher(BasePublisher):
    name = "facebook"
    circuit_name = "facebook"

    def __init__(self):
        self.graph_version = os.getenv("META_GRAPH_VERSION", "v23.0").strip()
        self.page_id = os.getenv("META_PAGE_ID", "").strip()
        self.page_access_token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()

    def is_configured(self) -> bool:
        return bool(self.page_id and self.page_access_token)

    def publish_text(self, content: str, **kwargs) -> dict:
        if not content or not content.strip():
            return self._result(False, self.name, error="Content cannot be empty.")
        if not self.page_id:
            return self._result(False, self.name, error="Facebook Page ID is not configured.")
        if not self.page_access_token:
            return self._result(False, self.name, error="Facebook Page access token is not configured.")

        url = f"https://graph.facebook.com/{self.graph_version}/{self.page_id}/feed"
        payload = {
            "message": content.strip(),
            "access_token": self.page_access_token,
        }
        try:
            response = self._safe_request("POST", url, timeout=TIMEOUT, data=payload)
            raw = self._parse_json_response(response)

            if response.status_code >= 400 or (isinstance(raw, dict) and raw.get("error")):
                error_msg = ""
                if isinstance(raw, dict) and raw.get("error"):
                    err = raw["error"]
                    error_msg = err.get("message", str(err))
                else:
                    error_msg = response.text[:200]
                return self._result(
                    False,
                    self.name,
                    error=f"Facebook API error: {error_msg}",
                    raw_response=raw if isinstance(raw, dict) else {},
                )

            post_id = str(raw.get("id", "")) if isinstance(raw, dict) else ""
            post_url = f"https://www.facebook.com/{post_id}" if post_id else ""
            return self._result(
                True,
                self.name,
                external_post_id=post_id,
                external_post_url=post_url,
                raw_response=raw if isinstance(raw, dict) else {},
            )
        except httpx.TimeoutException:
            return self._result(False, self.name, error="Facebook request timed out.")
        except Exception as exc:
            logger.warning("Facebook publish failed: %s", type(exc).__name__)
            return self._result(False, self.name, error=f"Facebook publish failed: {type(exc).__name__}")

    def publish_image(self, content: str, image_url: str, **kwargs) -> dict:
        return self.publish_text(content, **kwargs)

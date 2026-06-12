"""LinkedIn publisher via REST Posts API."""

import logging
import os

import httpx

from publishers.base import BasePublisher

logger = logging.getLogger(__name__)

TIMEOUT = 30.0


class LinkedInPublisher(BasePublisher):
    name = "linkedin"

    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
        self.author_urn = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
        self.api_version = os.getenv("LINKEDIN_API_VERSION", "202506").strip()

    def is_configured(self) -> bool:
        return bool(self.access_token and self.author_urn)

    def publish_text(self, content: str, **kwargs) -> dict:
        if not content or not content.strip():
            return self._result(False, self.name, error="Content cannot be empty.")
        if not self.access_token:
            return self._result(False, self.name, error="LinkedIn access token is not configured.")
        if not self.author_urn:
            return self._result(False, self.name, error="LinkedIn author URN is not configured.")

        payload = {
            "author": self.author_urn,
            "commentary": content.strip(),
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(
                    "https://api.linkedin.com/rest/posts",
                    json=payload,
                    headers=headers,
                )
            raw = {}
            try:
                raw = response.json()
            except Exception:
                raw = {"status_code": response.status_code, "text": response.text[:500]}

            if response.status_code >= 400:
                error_msg = raw.get("message", response.text[:200]) if isinstance(raw, dict) else response.text[:200]
                return self._result(
                    False,
                    self.name,
                    error=f"LinkedIn API error ({response.status_code}): {error_msg}",
                    raw_response=raw if isinstance(raw, dict) else {"text": str(raw)},
                )

            post_id = response.headers.get("x-restli-id", "")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else ""
            return self._result(
                True,
                self.name,
                external_post_id=post_id,
                external_post_url=post_url,
                raw_response=raw if isinstance(raw, dict) else {},
            )
        except httpx.TimeoutException:
            return self._result(False, self.name, error="LinkedIn request timed out.")
        except Exception as exc:
            logger.warning("LinkedIn publish failed: %s", type(exc).__name__)
            return self._result(False, self.name, error=f"LinkedIn publish failed: {type(exc).__name__}")

    def publish_image(self, content: str, image_url: str, **kwargs) -> dict:
        return self.publish_text(content, **kwargs)

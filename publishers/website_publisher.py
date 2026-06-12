"""Artixcore website CMS publisher."""

import logging
import os
import re

import httpx

from publishers.base import BasePublisher

logger = logging.getLogger(__name__)

TIMEOUT = 30.0


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:80] or "post"


class WebsitePublisher(BasePublisher):
    name = "website_blog"
    circuit_name = "website"

    def __init__(self):
        self.base_url = os.getenv("WEBSITE_API_BASE_URL", "").strip().rstrip("/")
        self.api_token = os.getenv("WEBSITE_API_TOKEN", "").strip()
        self.post_endpoint = os.getenv("WEBSITE_POST_ENDPOINT", "/api/posts").strip()

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_token)

    def publish_text(self, content: str, **kwargs) -> dict:
        if not content or not content.strip():
            return self._result(False, self.name, error="Content cannot be empty.")
        if not self.is_configured():
            return self._result(
                False,
                self.name,
                error="Website API is not configured. Set WEBSITE_API_BASE_URL and WEBSITE_API_TOKEN.",
            )

        title = kwargs.get("title") or kwargs.get("topic") or "Untitled Post"
        slug = kwargs.get("slug") or _slugify(str(title))
        meta_description = kwargs.get("meta_description", content.strip()[:160])

        payload = {
            "title": title,
            "slug": slug,
            "content": content.strip(),
            "meta_description": meta_description,
            "status": "draft",
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{self.post_endpoint}"
        try:
            response = self._safe_request(
                "POST", url, timeout=TIMEOUT, json=payload, headers=headers
            )
            raw = self._parse_json_response(response)

            if response.status_code >= 400:
                error_msg = ""
                if isinstance(raw, dict):
                    error_msg = raw.get("message", raw.get("error", response.text[:200]))
                else:
                    error_msg = response.text[:200]
                return self._result(
                    False,
                    self.name,
                    error=f"Website API error ({response.status_code}): {error_msg}",
                    raw_response=raw if isinstance(raw, dict) else {},
                )

            post_id = ""
            post_url = ""
            if isinstance(raw, dict):
                post_id = str(raw.get("id", raw.get("post_id", "")))
                post_url = str(raw.get("url", raw.get("permalink", "")))

            return self._result(
                True,
                self.name,
                external_post_id=post_id,
                external_post_url=post_url,
                raw_response=raw if isinstance(raw, dict) else {},
            )
        except httpx.TimeoutException:
            return self._result(False, self.name, error="Website API request timed out.")
        except Exception as exc:
            logger.warning("Website publish failed: %s", type(exc).__name__)
            return self._result(False, self.name, error=f"Website publish failed: {type(exc).__name__}")

    def publish_image(self, content: str, image_url: str, **kwargs) -> dict:
        return self.publish_text(content, image_url=image_url, **kwargs)

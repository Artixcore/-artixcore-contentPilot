"""Meta Instagram publisher (image posts, two-step flow)."""

import logging
import os

import httpx

from publishers.base import BasePublisher

logger = logging.getLogger(__name__)

TIMEOUT = 30.0


class MetaInstagramPublisher(BasePublisher):
    name = "instagram"
    circuit_name = "instagram"

    def __init__(self):
        self.graph_version = os.getenv("META_GRAPH_VERSION", "v23.0").strip()
        self.ig_user_id = os.getenv("META_IG_USER_ID", "").strip()
        self.page_access_token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()

    def is_configured(self) -> bool:
        return bool(self.ig_user_id and self.page_access_token)

    def publish_text(self, content: str, **kwargs) -> dict:
        image_url = kwargs.get("image_url", "")
        return self.publish_image(content, image_url, **kwargs)

    def publish_image(self, content: str, image_url: str, **kwargs) -> dict:
        if not content or not content.strip():
            return self._result(False, self.name, error="Caption cannot be empty.")
        if not image_url or not image_url.strip():
            return self._result(
                False,
                self.name,
                error="Instagram requires a public image URL. Please provide an image URL.",
            )
        if not self.ig_user_id:
            return self._result(False, self.name, error="Instagram user ID is not configured.")
        if not self.page_access_token:
            return self._result(False, self.name, error="Meta page access token is not configured.")

        base = f"https://graph.facebook.com/{self.graph_version}/{self.ig_user_id}"
        token = self.page_access_token
        try:
            media_resp = self._safe_request(
                "POST",
                f"{base}/media",
                timeout=TIMEOUT,
                data={
                    "image_url": image_url.strip(),
                    "caption": content.strip(),
                    "access_token": token,
                },
            )
            media_raw = self._parse_json_response(media_resp)

            if media_resp.status_code >= 400 or (isinstance(media_raw, dict) and media_raw.get("error")):
                error_msg = ""
                if isinstance(media_raw, dict) and media_raw.get("error"):
                    error_msg = media_raw["error"].get("message", str(media_raw["error"]))
                return self._result(
                    False,
                    self.name,
                    error=f"Instagram media creation failed: {error_msg or media_resp.text[:200]}",
                    raw_response=media_raw if isinstance(media_raw, dict) else {},
                )

            creation_id = str(media_raw.get("id", "")) if isinstance(media_raw, dict) else ""
            if not creation_id:
                return self._result(
                    False,
                    self.name,
                    error="Instagram did not return a creation ID from step 1.",
                    raw_response=media_raw if isinstance(media_raw, dict) else {},
                )

            publish_resp = self._safe_request(
                "POST",
                f"{base}/media_publish",
                timeout=TIMEOUT,
                data={"creation_id": creation_id, "access_token": token},
            )
            publish_raw = self._parse_json_response(publish_resp)

            if publish_resp.status_code >= 400 or (isinstance(publish_raw, dict) and publish_raw.get("error")):
                error_msg = ""
                if isinstance(publish_raw, dict) and publish_raw.get("error"):
                    error_msg = publish_raw["error"].get("message", str(publish_raw["error"]))
                return self._result(
                    False,
                    self.name,
                    error=f"Instagram publish failed: {error_msg or publish_resp.text[:200]}",
                    raw_response={"media": media_raw, "publish": publish_raw},
                )

            post_id = str(publish_raw.get("id", creation_id)) if isinstance(publish_raw, dict) else creation_id
            return self._result(
                True,
                self.name,
                external_post_id=post_id,
                external_post_url="",
                raw_response={"media": media_raw, "publish": publish_raw},
            )
        except httpx.TimeoutException:
            return self._result(False, self.name, error="Instagram request timed out.")
        except Exception as exc:
            logger.warning("Instagram publish failed: %s", type(exc).__name__)
            return self._result(False, self.name, error=f"Instagram publish failed: {type(exc).__name__}")

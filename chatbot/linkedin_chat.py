"""LinkedIn messaging connector (abstraction with MVP manual mode)."""

import logging
import os

import httpx

from core.utils import sanitize_payload

logger = logging.getLogger(__name__)

TIMEOUT = 30.0

LINKEDIN_MESSAGING_MSG = (
    "LinkedIn messaging requires approved API access. Configure valid permissions or use manual inbox mode."
)


class LinkedInChat:
    name = "linkedin"

    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
        self.author_urn = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
        self.api_version = os.getenv("LINKEDIN_API_VERSION", "202506").strip()
        self.messaging_enabled = os.getenv("LINKEDIN_MESSAGING_ENABLED", "false").lower() in ("true", "1", "yes")

    def is_configured(self) -> bool:
        return bool(self.access_token and self.author_urn)

    def get_status(self) -> dict:
        if not self.is_configured():
            return {
                "configured": False,
                "available": False,
                "message": "LinkedIn access token or author URN not configured.",
            }
        if not self.messaging_enabled:
            return {
                "configured": True,
                "available": False,
                "message": LINKEDIN_MESSAGING_MSG,
            }
        return {
            "configured": True,
            "available": True,
            "message": "LinkedIn messaging enabled (requires approved API access).",
        }

    def parse_incoming(self, payload: dict) -> list[dict]:
        return []

    def send_message(self, recipient_urn: str, text: str) -> dict:
        if not text or not text.strip():
            return {"success": False, "error": "Message cannot be empty.", "raw_response": {}}
        if not self.is_configured():
            return {"success": False, "error": "LinkedIn credentials are not configured.", "raw_response": {}}
        if not self.messaging_enabled:
            return {"success": False, "error": LINKEDIN_MESSAGING_MSG, "raw_response": {}}

        url = "https://api.linkedin.com/v2/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        payload = {
            "recipients": [recipient_urn],
            "subject": "Artixcore",
            "body": text.strip(),
        }
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(url, json=payload, headers=headers)
            raw = {}
            try:
                raw = response.json()
            except Exception:
                raw = {"status_code": response.status_code, "text": response.text[:500]}

            logger.info("LinkedIn send response: %s", sanitize_payload(raw))

            if response.status_code >= 400:
                error_msg = raw.get("message", response.text[:200]) if isinstance(raw, dict) else response.text[:200]
                return {
                    "success": False,
                    "error": f"LinkedIn API error: {error_msg}. {LINKEDIN_MESSAGING_MSG}",
                    "raw_response": raw,
                }
            return {"success": True, "error": "", "raw_response": raw}
        except httpx.TimeoutException:
            return {"success": False, "error": "LinkedIn request timed out.", "raw_response": {}}
        except Exception as exc:
            logger.warning("LinkedIn send failed: %s", type(exc).__name__)
            return {"success": False, "error": LINKEDIN_MESSAGING_MSG, "raw_response": {}}

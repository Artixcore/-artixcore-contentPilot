"""Facebook Messenger / Page messaging connector."""

import logging
import os
from typing import Any

import httpx

from core.utils import sanitize_payload

logger = logging.getLogger(__name__)

TIMEOUT = 30.0


class FacebookChat:
    name = "facebook"

    def __init__(self):
        self.graph_version = os.getenv("META_GRAPH_VERSION", "v23.0").strip()
        self.page_id = os.getenv("META_PAGE_ID", "").strip()
        self.page_access_token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
        self.verify_token = os.getenv("META_VERIFY_TOKEN", "").strip()

    def is_configured(self) -> bool:
        return bool(self.page_id and self.page_access_token)

    def get_status(self) -> dict:
        if self.is_configured():
            return {
                "configured": True,
                "available": True,
                "message": "Facebook Page messaging configured.",
            }
        missing = []
        if not self.page_id:
            missing.append("META_PAGE_ID")
        if not self.page_access_token:
            missing.append("META_PAGE_ACCESS_TOKEN")
        return {
            "configured": False,
            "available": False,
            "message": f"Missing: {', '.join(missing)}",
        }

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str | None:
        if mode == "subscribe" and token == self.verify_token and self.verify_token:
            return challenge
        return None

    def parse_webhook_payload(self, payload: dict[str, Any]) -> list[dict]:
        messages = []
        try:
            for entry in payload.get("entry", []):
                for messaging in entry.get("messaging", []):
                    sender = messaging.get("sender", {})
                    message = messaging.get("message", {})
                    text = message.get("text", "")
                    if not text:
                        continue
                    messages.append(
                        {
                            "user_platform_id": str(sender.get("id", "")),
                            "platform_message_id": str(message.get("mid", "")),
                            "message_text": text,
                            "platform_conversation_id": str(sender.get("id", "")),
                        }
                    )
        except Exception as exc:
            logger.warning("Facebook webhook parse failed: %s", type(exc).__name__)
        return messages

    def send_message(self, recipient_id: str, text: str) -> dict:
        if not text or not text.strip():
            return {"success": False, "error": "Message cannot be empty.", "raw_response": {}}
        if not self.page_access_token:
            return {"success": False, "error": "Facebook Page access token is not configured.", "raw_response": {}}
        if not recipient_id:
            return {"success": False, "error": "Recipient ID is required.", "raw_response": {}}

        url = f"https://graph.facebook.com/{self.graph_version}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text.strip()},
            "access_token": self.page_access_token,
        }
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(url, json=payload)
            raw = {}
            try:
                raw = response.json()
            except Exception:
                raw = {"status_code": response.status_code, "text": response.text[:500]}

            logger.info("Facebook send response: %s", sanitize_payload(raw))

            if response.status_code >= 400 or (isinstance(raw, dict) and raw.get("error")):
                error_msg = ""
                if isinstance(raw, dict) and raw.get("error"):
                    err = raw["error"]
                    error_msg = err.get("message", str(err))
                else:
                    error_msg = response.text[:200]
                return {"success": False, "error": f"Facebook API error: {error_msg}", "raw_response": raw}

            return {"success": True, "error": "", "raw_response": raw}
        except httpx.TimeoutException:
            return {"success": False, "error": "Facebook request timed out.", "raw_response": {}}
        except Exception as exc:
            logger.warning("Facebook send failed: %s", type(exc).__name__)
            return {"success": False, "error": f"Facebook send failed: {type(exc).__name__}", "raw_response": {}}

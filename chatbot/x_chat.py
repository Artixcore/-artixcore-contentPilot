"""X / Twitter DM and mention reply connector."""

import logging
import os

import httpx

from core.utils import sanitize_payload

logger = logging.getLogger(__name__)

TIMEOUT = 30.0
MAX_LENGTH = 280


class XChat:
    name = "twitter"

    def __init__(self):
        self.access_token = os.getenv("X_ACCESS_TOKEN", "").strip()
        self.dm_enabled = os.getenv("X_DM_ENABLED", "false").lower() in ("true", "1", "yes")

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def get_status(self) -> dict:
        if not self.access_token:
            return {
                "configured": False,
                "available": False,
                "message": "X access token is not configured.",
            }
        if not self.dm_enabled:
            return {
                "configured": True,
                "available": True,
                "message": "X token configured. DM replies require X_DM_ENABLED and appropriate API access.",
            }
        return {
            "configured": True,
            "available": True,
            "message": "X messaging configured.",
        }

    def send_reply(self, tweet_id: str, text: str) -> dict:
        if not text or not text.strip():
            return {"success": False, "error": "Message cannot be empty.", "raw_response": {}}
        if not self.access_token:
            return {"success": False, "error": "X access token is not configured.", "raw_response": {}}
        if len(text.strip()) > MAX_LENGTH:
            return {
                "success": False,
                "error": f"X replies must be {MAX_LENGTH} characters or fewer.",
                "raw_response": {},
            }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"text": text.strip(), "reply": {"in_reply_to_tweet_id": tweet_id}} if tweet_id else {"text": text.strip()}
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(
                    "https://api.x.com/2/tweets",
                    json=payload,
                    headers=headers,
                )
            raw = {}
            try:
                raw = response.json()
            except Exception:
                raw = {"status_code": response.status_code, "text": response.text[:500]}

            logger.info("X send response: %s", sanitize_payload(raw))

            if response.status_code >= 400:
                error_msg = ""
                if isinstance(raw, dict):
                    errors = raw.get("errors", [])
                    if errors:
                        error_msg = errors[0].get("detail", errors[0].get("message", ""))
                    if not error_msg:
                        error_msg = raw.get("detail", response.text[:200])
                else:
                    error_msg = response.text[:200]
                return {
                    "success": False,
                    "error": f"X API error: {error_msg}",
                    "raw_response": raw if isinstance(raw, dict) else {},
                }
            return {"success": True, "error": "", "raw_response": raw if isinstance(raw, dict) else {}}
        except httpx.TimeoutException:
            return {"success": False, "error": "X request timed out.", "raw_response": {}}
        except Exception as exc:
            logger.warning("X send failed: %s", type(exc).__name__)
            return {"success": False, "error": f"X send failed: {type(exc).__name__}", "raw_response": {}}

    def send_dm(self, participant_id: str, text: str) -> dict:
        if not self.dm_enabled:
            return {
                "success": False,
                "error": "X DM API access is not enabled. Set X_DM_ENABLED=true if your API tier supports DMs.",
                "raw_response": {},
            }
        return self.send_reply("", text)

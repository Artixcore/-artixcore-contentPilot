"""Base publisher abstraction for social platforms."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from core.circuit_breaker import circuit_call
from core.load_manager import DEFAULT_API_TIMEOUT_SECONDS
from core.retries import retry_with_backoff
from core.utils import sanitize_payload

logger = logging.getLogger(__name__)


class BasePublisher:
    name: str = "base"
    circuit_name: str = "website"

    def is_configured(self) -> bool:
        raise NotImplementedError

    def publish_text(self, content: str, **kwargs) -> dict:
        raise NotImplementedError

    def publish_image(self, content: str, image_url: str, **kwargs) -> dict:
        raise NotImplementedError

    def _result(
        self,
        success: bool,
        platform: str,
        external_post_id: str = "",
        external_post_url: str = "",
        error: str = "",
        raw_response: dict | None = None,
    ) -> dict:
        return {
            "success": success,
            "platform": platform,
            "external_post_id": external_post_id,
            "external_post_url": external_post_url,
            "error": error,
            "raw_response": raw_response or {},
        }

    def _safe_request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | None = None,
        **kwargs,
    ) -> httpx.Response:
        """HTTP request with timeout, circuit breaker, and retry for 5xx."""

        timeout = timeout or float(DEFAULT_API_TIMEOUT_SECONDS)
        breaker = self.circuit_name or self.name

        def _do_request() -> httpx.Response:
            with httpx.Client(timeout=timeout) as client:
                return client.request(method, url, **kwargs)

        def _call_with_retry() -> httpx.Response:
            def _attempt() -> httpx.Response:
                response = _do_request()
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                return response

            return retry_with_backoff(_attempt, retries=2, base_delay=1.0, max_delay=5.0)

        try:
            return circuit_call(breaker, _call_with_retry)
        except httpx.TimeoutException:
            raise
        except httpx.HTTPError:
            raise

    def _parse_json_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
            return data if isinstance(data, dict) else {"data": data}
        except Exception:
            return {"status_code": response.status_code, "text": response.text[:500]}

    def _log_failure(self, action: str, error: str, raw: dict | None = None) -> None:
        logger.warning(
            "Publisher %s %s failed: %s payload=%s",
            self.name,
            action,
            error,
            sanitize_payload(raw or {}),
        )

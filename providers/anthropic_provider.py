"""Anthropic provider implementation."""

import logging
import os
import time

from core.circuit_breaker import circuit_call
from core.errors import AuthenticationConfigError
from core.load_manager import DEFAULT_API_TIMEOUT_SECONDS, with_load_slot
from core.rate_limiter import check_rate_limit
from core.retries import retry_with_backoff
from providers.base import BaseAIProvider, GenerationResult, ProviderError

logger = logging.getLogger(__name__)


def _map_anthropic_error(exc: Exception) -> ProviderError:
    name = type(exc).__name__
    msg = str(exc).lower()
    if "timeout" in name.lower() or "timeout" in msg:
        return ProviderError("Anthropic request timed out. Please try again.", provider="anthropic")
    if "ratelimit" in name.lower() or "rate limit" in msg or "429" in msg:
        return ProviderError("Anthropic rate limit reached. Please wait and try again.", provider="anthropic")
    if "authentication" in msg or ("invalid" in msg and "key" in msg) or "401" in msg:
        return ProviderError("Anthropic API key is invalid. Please check your ANTHROPIC_API_KEY.", provider="anthropic")
    if "not_found" in msg or ("model" in msg and "404" in msg):
        return ProviderError("Anthropic model not found. Check your ANTHROPIC_MODEL setting.", provider="anthropic")
    if "connection" in msg or "network" in msg:
        return ProviderError("Network error connecting to Anthropic. Check your connection.", provider="anthropic")
    if "content" in msg and ("filter" in msg or "policy" in msg):
        return ProviderError("Anthropic blocked the content due to safety filters.", provider="anthropic")
    return ProviderError(f"Anthropic request failed: {name}", provider="anthropic")


class AnthropicProvider(BaseAIProvider):
    name = "anthropic"

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest").strip()
        self.timeout = float(os.getenv("DEFAULT_API_TIMEOUT_SECONDS", str(DEFAULT_API_TIMEOUT_SECONDS)))

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def model_name(self) -> str:
        return self.model

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> GenerationResult:
        if not self.is_available():
            raise AuthenticationConfigError(
                "Anthropic API key is not configured.",
                user_action="Add ANTHROPIC_API_KEY to your .env file.",
            )

        check_rate_limit("ai_generation", key="anthropic")
        start = time.perf_counter()
        max_tokens = kwargs.get("max_tokens", 4096)
        temperature = kwargs.get("temperature", 0.7)

        def _call_api():
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
            return client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt or "You are a helpful content assistant.",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )

        try:
            with with_load_slot("ai"):
                response = circuit_call(
                    "anthropic",
                    lambda: retry_with_backoff(_call_api, retries=2, base_delay=1.0),
                )
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            if not text.strip():
                raise ProviderError("Anthropic returned empty content.", provider=self.name)
            latency = int((time.perf_counter() - start) * 1000)
            usage = response.usage
            token_in = usage.input_tokens if usage else None
            token_out = usage.output_tokens if usage else None
            return GenerationResult(
                text=text,
                provider=self.name,
                model=self.model,
                latency_ms=latency,
                success=True,
                token_input_estimate=token_in,
                token_output_estimate=token_out,
                raw_response={
                    "model": self.model,
                    "usage": {"input_tokens": token_in, "output_tokens": token_out},
                },
            )
        except ProviderError:
            raise
        except AuthenticationConfigError:
            raise
        except Exception as exc:
            logger.warning("Anthropic generation failed: %s", type(exc).__name__)
            raise _map_anthropic_error(exc) from exc

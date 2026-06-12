"""OpenAI provider implementation."""

import logging
import os
import time

from core.circuit_breaker import circuit_call
from core.errors import AIProviderError, AuthenticationConfigError
from core.load_manager import DEFAULT_API_TIMEOUT_SECONDS, with_load_slot
from core.rate_limiter import check_rate_limit
from core.retries import retry_with_backoff
from providers.base import BaseAIProvider, GenerationResult, ProviderError

logger = logging.getLogger(__name__)

SENSITIVE_PATTERNS = (
    "invalid_api_key",
    "authentication",
    "incorrect api key",
    "invalid api key",
)


def _map_openai_error(exc: Exception) -> ProviderError:
    name = type(exc).__name__
    msg = str(exc).lower()
    if "timeout" in name.lower() or "timeout" in msg:
        return ProviderError("OpenAI request timed out. Please try again.", provider="openai")
    if "ratelimit" in name.lower() or "rate limit" in msg or "429" in msg:
        return ProviderError("OpenAI rate limit reached. Please wait and try again.", provider="openai")
    if any(p in msg for p in SENSITIVE_PATTERNS) or "401" in msg:
        return ProviderError("OpenAI API key is invalid. Please check your OPENAI_API_KEY.", provider="openai")
    if "not found" in msg or ("model" in msg and "404" in msg):
        return ProviderError("OpenAI model not found. Check your OPENAI_MODEL setting.", provider="openai")
    if "connection" in msg or "network" in msg:
        return ProviderError("Network error connecting to OpenAI. Check your connection.", provider="openai")
    if "content" in msg and ("filter" in msg or "policy" in msg):
        return ProviderError("OpenAI blocked the content due to safety filters.", provider="openai")
    return ProviderError(f"OpenAI request failed: {name}", provider="openai")


class OpenAIProvider(BaseAIProvider):
    name = "openai"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
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
                "OpenAI API key is not configured.",
                user_action="Add OPENAI_API_KEY to your .env file.",
            )

        check_rate_limit("ai_generation", key="openai")
        start = time.perf_counter()
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)

        def _call_api():
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, timeout=self.timeout)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        try:
            with with_load_slot("ai"):
                response = circuit_call(
                    "openai",
                    lambda: retry_with_backoff(_call_api, retries=2, base_delay=1.0),
                )
            if not response.choices:
                raise ProviderError("OpenAI returned an empty response.", provider=self.name)
            text = response.choices[0].message.content or ""
            if not text.strip():
                raise ProviderError("OpenAI returned empty content.", provider=self.name)
            latency = int((time.perf_counter() - start) * 1000)
            usage = response.usage
            token_in = usage.prompt_tokens if usage else None
            token_out = usage.completion_tokens if usage else None
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
                    "usage": {"prompt_tokens": token_in, "completion_tokens": token_out},
                },
            )
        except ProviderError:
            raise
        except AuthenticationConfigError:
            raise
        except Exception as exc:
            logger.warning("OpenAI generation failed: %s", type(exc).__name__)
            mapped = _map_openai_error(exc)
            raise mapped from exc

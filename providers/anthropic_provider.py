"""Anthropic provider implementation."""

import logging
import os
import time

from providers.base import BaseAIProvider, GenerationResult, ProviderError

logger = logging.getLogger(__name__)


def _friendly_error(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc).lower()
    if "timeout" in name.lower() or "timeout" in msg:
        return "Anthropic request timed out. Please try again."
    if "ratelimit" in name.lower() or "rate limit" in msg or "429" in msg:
        return "Anthropic rate limit reached. Please wait and try again."
    if "authentication" in msg or "invalid" in msg and "key" in msg or "401" in msg:
        return "Anthropic API key is invalid. Please check your ANTHROPIC_API_KEY."
    if "not_found" in msg or "model" in msg and "404" in msg:
        return "Anthropic model not found. Check your ANTHROPIC_MODEL setting."
    if "connection" in msg or "network" in msg:
        return "Network error connecting to Anthropic. Check your connection."
    return f"Anthropic request failed: {name}"


class AnthropicProvider(BaseAIProvider):
    name = "anthropic"

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest").strip()

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
            raise ProviderError("Anthropic API key is not configured.", provider=self.name)

        start = time.perf_counter()
        max_tokens = kwargs.get("max_tokens", 4096)
        temperature = kwargs.get("temperature", 0.7)
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key, timeout=60.0)
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt or "You are a helpful content assistant.",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
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
                raw_response={"model": self.model, "usage": {
                    "input_tokens": token_in,
                    "output_tokens": token_out,
                }},
            )
        except Exception as exc:
            logger.warning("Anthropic generation failed: %s", type(exc).__name__)
            raise ProviderError(_friendly_error(exc), provider=self.name) from exc

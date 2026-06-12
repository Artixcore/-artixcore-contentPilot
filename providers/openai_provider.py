"""OpenAI provider implementation."""

import logging
import os
import time

from providers.base import BaseAIProvider, GenerationResult, ProviderError

logger = logging.getLogger(__name__)

SENSITIVE_PATTERNS = (
    "invalid_api_key",
    "authentication",
    "incorrect api key",
    "invalid api key",
)


def _friendly_error(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc).lower()
    if "timeout" in name.lower() or "timeout" in msg:
        return "OpenAI request timed out. Please try again."
    if "ratelimit" in name.lower() or "rate limit" in msg or "429" in msg:
        return "OpenAI rate limit reached. Please wait and try again."
    if any(p in msg for p in SENSITIVE_PATTERNS) or "401" in msg:
        return "OpenAI API key is invalid. Please check your OPENAI_API_KEY."
    if "not found" in msg or "model" in msg and "404" in msg:
        return "OpenAI model not found. Check your OPENAI_MODEL setting."
    if "connection" in msg or "network" in msg:
        return "Network error connecting to OpenAI. Check your connection."
    return f"OpenAI request failed: {name}"


class OpenAIProvider(BaseAIProvider):
    name = "openai"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

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
            raise ProviderError("OpenAI API key is not configured.", provider=self.name)

        start = time.perf_counter()
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, timeout=60.0)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content or ""
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
                raw_response={"model": self.model, "usage": {
                    "prompt_tokens": token_in,
                    "completion_tokens": token_out,
                }},
            )
        except Exception as exc:
            logger.warning("OpenAI generation failed: %s", type(exc).__name__)
            raise ProviderError(_friendly_error(exc), provider=self.name) from exc

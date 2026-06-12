"""Anthropic provider implementation."""

import logging
import os
import time

from providers.base import BaseAIProvider, GenerationResult, ProviderError

logger = logging.getLogger(__name__)


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
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key, timeout=60.0)
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4096),
                system=system_prompt or "You are a helpful content assistant.",
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
            )
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            latency = int((time.perf_counter() - start) * 1000)
            return GenerationResult(
                text=text,
                provider=self.name,
                model=self.model,
                latency_ms=latency,
                success=True,
            )
        except Exception as exc:
            logger.warning("Anthropic generation failed: %s", type(exc).__name__)
            raise ProviderError(
                f"Anthropic request failed: {type(exc).__name__}",
                provider=self.name,
            ) from exc

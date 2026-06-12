"""OpenAI provider implementation."""

import logging
import os
import time

from providers.base import BaseAIProvider, GenerationResult, ProviderError

logger = logging.getLogger(__name__)


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
        try:
            from openai import APIError, APITimeoutError, OpenAI

            client = OpenAI(api_key=self.api_key, timeout=60.0)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
            )
            text = response.choices[0].message.content or ""
            latency = int((time.perf_counter() - start) * 1000)
            return GenerationResult(
                text=text,
                provider=self.name,
                model=self.model,
                latency_ms=latency,
                success=True,
            )
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            logger.warning("OpenAI generation failed: %s", type(exc).__name__)
            raise ProviderError(
                f"OpenAI request failed: {type(exc).__name__}",
                provider=self.name,
            ) from exc

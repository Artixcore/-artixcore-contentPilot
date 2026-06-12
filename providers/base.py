"""Base AI provider abstraction."""

from dataclasses import dataclass
from typing import Optional


class ProviderError(Exception):
    """Raised when a provider fails to generate content."""

    def __init__(self, message: str, provider: str = ""):
        super().__init__(message)
        self.provider = provider
        self.message = message


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None


class BaseAIProvider:
    name: str = "base"

    def is_available(self) -> bool:
        raise NotImplementedError

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> GenerationResult:
        raise NotImplementedError

    @property
    def model_name(self) -> str | None:
        return None

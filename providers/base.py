"""Base AI provider abstraction."""

from dataclasses import dataclass, field
from typing import Any, Optional


class ProviderError(Exception):
    """Raised when a provider fails to generate content."""

    def __init__(self, message: str, provider: str = ""):
        super().__init__(message)
        self.provider = provider
        self.message = message


class ProviderUnavailableError(Exception):
    """Raised when no real AI provider is configured."""

    def __init__(self, message: str | None = None):
        from providers import PROVIDER_UNAVAILABLE_MSG

        super().__init__(message or PROVIDER_UNAVAILABLE_MSG)
        self.message = message or PROVIDER_UNAVAILABLE_MSG


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    token_input_estimate: Optional[int] = None
    token_output_estimate: Optional[int] = None
    raw_response: Optional[dict[str, Any]] = field(default=None)


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

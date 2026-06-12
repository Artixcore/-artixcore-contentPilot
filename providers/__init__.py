"""AI provider registry."""

from providers.anthropic_provider import AnthropicProvider
from providers.base import BaseAIProvider
from providers.openai_provider import OpenAIProvider

PROVIDER_UNAVAILABLE_MSG = (
    "Please provide a valid OpenAI or Anthropic API key to use Artixcore ContentPilot."
)


def get_all_providers() -> dict[str, BaseAIProvider]:
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
    }

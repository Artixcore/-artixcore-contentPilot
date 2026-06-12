"""AI provider registry."""

from providers.anthropic_provider import AnthropicProvider
from providers.base import BaseAIProvider
from providers.mock_provider import MockProvider
from providers.openai_provider import OpenAIProvider


def get_all_providers() -> dict[str, BaseAIProvider]:
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "mock": MockProvider(),
    }
